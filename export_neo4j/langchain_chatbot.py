# langchain_chatbot.py
"""
Lightweight ShrimpExportChatbot:
- Uses OpenAI (openai package) to generate a single read-only Cypher query
- Executes the Cypher via neo4j.Driver
- Summarizes results using the LLM (optional)
- Returns {'cypher_query': ..., 'answer': ..., 'rows': [...]}
"""

import re
import json
import os
import logging
from typing import List, Dict, Any, Optional

import openai
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Safety patterns: disallow destructive / procedure / file / admin statements
_FORBIDDEN_PATTERNS = [
    r"\bDELETE\b", r"\bDETACH\s+DELETE\b", r"\bREMOVE\b", r"\bSET\b\s+\w+:",
    r"\bCREATE\b", r"\bMERGE\b", r"\bCALL\b", r"\bapoc\.", r"\bLOAD\s+CSV\b",
    r"\bDROP\b", r"\bCONSTRAINT\b", r"\bINDEX\b", r"\bALTER\b", r"\bdbms\."
]
_forbidden_re = re.compile("|".join(_FORBIDDEN_PATTERNS), flags=re.IGNORECASE)

SCHEMA_TEXT = """
Labels: Shipment(shipment_id, invoice_no, date, year_month, fob_usd),
        Exporter(iec, name),
        Product(hs_code, hs_code_description),
        Consignee(consignee_id, name, address),
        Country(iso_code_2, name),
        IndianPort(port_code, port_name),
        DestinationPort(port_name),
        TimeMonth(year_month)
Relationships: (Exporter)-[:SHIPPED]->(Shipment),
               (Shipment)-[:CONTAINS]->(Product),
               (Shipment)-[:SENT_TO]->(Consignee),
               (Shipment)-[:EXPORTED_TO]->(Country),
               (Consignee)-[:LOCATED_IN]->(Country),
               (Shipment)-[:DEPARTED_FROM]->(IndianPort),
               (Shipment)-[:ARRIVED_AT]->(DestinationPort),
               (Shipment)-[:OCCURRED_IN]->(TimeMonth)
Notes: Use only read-only MATCH/RETURN queries. Use year_month strings like '2023-12' to filter TimeMonth.
"""

class ShrimpExportChatbot:
    def __init__(
        self,
        neo4j_uri: str,
        neo4j_user: str,
        neo4j_password: str,
        openai_api_key: str,
        model_name: str = "gpt-4",
        max_result_rows: int = 200,
    ):
        if not neo4j_uri or not neo4j_user or not neo4j_password:
            raise ValueError("Please provide neo4j_uri, neo4j_user and neo4j_password")

        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        openai.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OpenAI API key not provided (openai_api_key or OPENAI_API_KEY env)")

        self.model_name = model_name or "gpt-4"
        self.max_result_rows = max_result_rows

    def close(self):
        try:
            self.driver.close()
        except Exception:
            pass
        
    def validate_connection(self) -> bool:
        """Validate Neo4j connection"""
        try:
            with self.driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count LIMIT 1")
                record = result.single()
                if record:
                    count = record["count"]
                    logger.info(f"✓ Neo4j connection successful. Total nodes: {count}")
                    return True
                return False
        except Exception as e:
            logger.error(f"✗ Neo4j connection failed: {e}")
            return False
    
    def get_schema_info(self) -> str:
        """Get the current graph schema"""
        return SCHEMA_TEXT 

    def _generate_cypher(self, question: str) -> str:
        """
        Ask the LLM to emit only a single Cypher query (READ-ONLY).
        The model response should be the raw Cypher (no surrounding explanation).
        """
        system = (
            "You are an assistant that returns **a single, read-only Cypher query** "
            "that answers the user's question given the database schema. "
            "Output ONLY the Cypher query and nothing else. "
            "The query must be safe (no CREATE, MERGE, DELETE, CALL, apoc.*, LOAD CSV, DROP, CONSTRAINT, INDEX, etc.)."
        )
        user = f"Schema:\n{SCHEMA_TEXT}\n\nQuestion: {question}\n\nReturn only the Cypher query."
        try:
            resp = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.0,
                max_tokens=600,
            )
        except Exception as e:
            logger.exception("OpenAI request failed")
            raise

        cypher = resp["choices"][0]["message"]["content"].strip()
        # If the LLM returned markdown code fences, unwrap them
        if cypher.startswith("```"):
            cypher = "\n".join(cypher.splitlines()[1:-1]).strip()
        return cypher

    def _is_safe_cypher(self, cypher: str) -> bool:
        if _forbidden_re.search(cypher):
            return False
        # require MATCH or RETURN at least
        if not re.search(r"\bMATCH\b", cypher, flags=re.IGNORECASE) and not re.search(r"\bRETURN\b", cypher, flags=re.IGNORECASE):
            return False
        return True

    def _run_cypher(self, cypher: str) -> List[Dict[str, Any]]:
        """
        Execute cypher and return list of dict rows (limited to max_result_rows)
        """
        rows = []
        with self.driver.session() as session:
            result = session.run(cypher)
            count = 0
            for record in result:
                rows.append(record.data())
                count += 1
                if count >= self.max_result_rows:
                    break
        return rows

    def _summarize_results(self, question: str, cypher: str, rows: List[Dict[str, Any]]) -> str:
        """
        Ask the LLM to summarize the rows for the user. Provide a small (truncated) JSON preview.
        """
        preview = rows[:40]  # limit how much we feed the model
        system = "You are a helpful assistant that summarizes tabular query results in concise, plain English."
        user = (
            f"Question: {question}\n\n"
            f"Cypher used:\n{cypher}\n\n"
            f"Rows (JSON array, truncated):\n{json.dumps(preview, default=str)}\n\n"
            "Provide a short summary answer (2-6 sentences). If the rows are empty, say 'No results found.'"
        )
        try:
            resp = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.0,
                max_tokens=400,
            )
            ans = resp["choices"][0]["message"]["content"].strip()
            return ans
        except Exception as e:
            logger.exception("OpenAI summarization failed; falling back to raw rows")
            return f"Could not summarize results: showing raw rows. Rows count: {len(rows)}"

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Main entrypoint.
        Returns: {'cypher_query': str, 'answer': str, 'rows': List[dict]}
        """
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty")

        # 1) generate cypher
        cypher = self._generate_cypher(question)
        logger.info("Generated cypher:\n%s", cypher)

        # 2) safety check
        if not self._is_safe_cypher(cypher):
            logger.error("Generated Cypher failed safety checks")
            raise ValueError("Generated Cypher failed safety checks; refusing to run it.\nCypher:\n" + cypher)

        # 3) run cypher
        try:
            rows = self._run_cypher(cypher)
        except Exception as e:
            logger.exception("Error executing Cypher")
            raise RuntimeError(f"Error executing Cypher: {e}")

        # 4) get human-friendly answer
        answer = self._summarize_results(question, cypher, rows) if rows else "No results found."

        return {"cypher_query": cypher, "answer": answer, "rows": rows}
