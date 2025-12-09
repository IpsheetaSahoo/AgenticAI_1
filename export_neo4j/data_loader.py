"""
CSV to Neo4j Data Loader for Shrimp Export Data
Loads data from CSV into Neo4j graph database with proper relationships
"""

import pandas as pd
from neo4j import GraphDatabase
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ShrimpDataLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.batch_size = 500
    
    def close(self):
        self.driver.close()
    
    @staticmethod
    def generate_consignee_id(name: str, address: str) -> str:
        """Generate unique ID for consignee based on name and address"""
        combined = f"{name}_{address}".lower().strip()
        return hashlib.md5(combined.encode()).hexdigest()
    
    @staticmethod
    def parse_date(date_str) -> Dict[str, Any]:
        """Parse date and extract year, month, year_month, quarter"""
        try:
            if pd.isna(date_str):
                return None
            
            date_obj = pd.to_datetime(date_str)
            return {
                'date': date_obj.strftime('%Y-%m-%d'),
                'year': date_obj.year,
                'month': date_obj.month,
                'year_month': date_obj.strftime('%Y-%m'),
                'quarter': f"Q{(date_obj.month-1)//3 + 1}"
            }
        except Exception as e:
            logger.warning(f"Error parsing date {date_str}: {e}")
            return None
    
    @staticmethod
    def clean_numeric(value) -> float:
        """Clean and convert numeric values"""
        try:
            if pd.isna(value):
                return 0.0
            return float(value)
        except:
            return 0.0
    
    @staticmethod
    def clean_string(value) -> str:
        """Clean string values"""
        try:
            if pd.isna(value):
                return None
            return str(value).strip()
        except:
            return None
    
    def load_data_from_csv(self, csv_path: str):
        """Load data from CSV file"""
        logger.info(f"Reading CSV file: {csv_path}")
        
        # Read CSV with proper column handling
        df = pd.read_csv(csv_path, low_memory=False)
        
        logger.info(f"Loaded {len(df)} rows from CSV")
        logger.info(f"Columns found: {len(df.columns)}")
        
        # Clean column names (remove extra spaces)
        df.columns = df.columns.str.strip()
        
        return df
    
    def create_time_months(self, session, df):
        """Create TimeMonth nodes"""
        logger.info("Creating TimeMonth nodes...")
        
        unique_months = df['DATE'].apply(lambda x: self.parse_date(x)).dropna()
        unique_months = pd.DataFrame(unique_months.tolist()).drop_duplicates(subset=['year_month'])
        
        for _, row in unique_months.iterrows():
            query = """
            MERGE (tm:TimeMonth {year_month: $year_month})
            ON CREATE SET 
                tm.year = $year,
                tm.month = $month,
                tm.quarter = $quarter
            """
            session.run(query, 
                year_month=row['year_month'],
                year=int(row['year']),
                month=int(row['month']),
                quarter=row['quarter']
            )
        
        logger.info(f"Created {len(unique_months)} TimeMonth nodes")
    
    def create_products(self, session, df):
        """Create Product nodes"""
        logger.info("Creating Product nodes...")
        
        # Get unique HS codes
        products = df[['HS CODE', 'HS CODE_2', 'HS CODE_4', 'HS CODE_DESCRIPTION']].drop_duplicates(subset=['HS CODE'])
        
        for _, row in products.iterrows():
            query = """
            MERGE (p:Product {hs_code: $hs_code})
            ON CREATE SET 
                p.hs_code_2 = $hs_code_2,
                p.hs_code_4 = $hs_code_4,
                p.hs_code_description = $hs_code_description
            """
            session.run(query,
                hs_code=self.clean_string(row['HS CODE']),
                hs_code_2=self.clean_string(row['HS CODE_2']),
                hs_code_4=self.clean_string(row['HS CODE_4']),
                hs_code_description=self.clean_string(row['HS CODE_DESCRIPTION'])
            )
        
        logger.info(f"Created {len(products)} Product nodes")
    
    def create_exporters(self, session, df):
        """Create Exporter nodes"""
        logger.info("Creating Exporter nodes...")
        
        exporters = df[['IEC', 'EXPORTER', 'ADDRESS', 'CITY', 'PIN']].drop_duplicates(subset=['IEC'])
        
        for _, row in exporters.iterrows():
            query = """
            MERGE (e:Exporter {iec: $iec})
            ON CREATE SET 
                e.name = $name,
                e.address = $address,
                e.city = $city,
                e.pin = $pin
            """
            session.run(query,
                iec=self.clean_string(row['IEC']),
                name=self.clean_string(row['EXPORTER']),
                address=self.clean_string(row['ADDRESS']),
                city=self.clean_string(row['CITY']),
                pin=self.clean_string(row['PIN'])
            )
        
        logger.info(f"Created {len(exporters)} Exporter nodes")
    
    def create_consignees(self, session, df):
        """Create Consignee nodes"""
        logger.info("Creating Consignee nodes...")
        
        # Generate consignee IDs
        df['consignee_id'] = df.apply(
            lambda row: self.generate_consignee_id(
                self.clean_string(row['CONSIGNEE NAME']) or '',
                self.clean_string(row['CONSIGNEE ADDRESS']) or ''
            ), axis=1
        )
        
        consignees = df[['consignee_id', 'CONSIGNEE NAME', 'CONSIGNEE ADDRESS']].drop_duplicates(subset=['consignee_id'])
        
        for _, row in consignees.iterrows():
            query = """
            MERGE (c:Consignee {consignee_id: $consignee_id})
            ON CREATE SET 
                c.name = $name,
                c.address = $address
            """
            session.run(query,
                consignee_id=row['consignee_id'],
                name=self.clean_string(row['CONSIGNEE NAME']),
                address=self.clean_string(row['CONSIGNEE ADDRESS'])
            )
        
        logger.info(f"Created {len(consignees)} Consignee nodes")
    
    def create_countries(self, session, df):
        """Create Country nodes"""
        logger.info("Creating Country nodes...")
        
        countries = df[['COUNTRY', 'country iso_code_2']].drop_duplicates(subset=['country iso_code_2'])
        
        count = 0
        for _, row in countries.iterrows():
            iso_code = self.clean_string(row['country iso_code_2'])
            if iso_code:
                query = """
                MERGE (c:Country {iso_code_2: $iso_code})
                ON CREATE SET c.name = $name
                """
                session.run(query,
                    iso_code=iso_code,
                    name=self.clean_string(row['COUNTRY'])
                )
                count += 1
        
        logger.info(f"Created {count} Country nodes")
    
    def create_ports(self, session, df):
        """Create IndianPort and DestinationPort nodes"""
        logger.info("Creating Port nodes...")
        
        # Indian Ports
        indian_ports = df[['INDIAN PORT', 'PORT CODE']].drop_duplicates(subset=['PORT CODE'])
        indian_count = 0
        for _, row in indian_ports.iterrows():
            port_code = self.clean_string(row['PORT CODE'])
            if port_code:
                query = """
                MERGE (ip:IndianPort {port_code: $port_code})
                ON CREATE SET ip.port_name = $port_name
                """
                session.run(query,
                    port_code=port_code,
                    port_name=self.clean_string(row['INDIAN PORT'])
                )
                indian_count += 1
        
        # Destination Ports
        dest_ports = df[['DESTINATION PORT']].drop_duplicates()
        dest_count = 0
        for _, row in dest_ports.iterrows():
            port_name = self.clean_string(row['DESTINATION PORT'])
            if port_name:
                query = """
                MERGE (dp:DestinationPort {port_name: $port_name})
                """
                session.run(query, port_name=port_name)
                dest_count += 1
        
        logger.info(f"Created {indian_count} IndianPort nodes and {dest_count} DestinationPort nodes")
    
    def create_shipments_and_relationships(self, session, df):
        """
        Safer, split-queries approach for creating Shipment nodes and relationships.
        Replace your existing method with this. Logs failing rows to failed_rows.csv.
        """
        import csv

        logger.info("Creating unique constraints (if not exists)...")
        # Neo4j 4+ style constraints — safe to call repeatedly
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Shipment) REQUIRE s.shipment_id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Exporter) REQUIRE e.iec IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Product) REQUIRE p.hs_code IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Consignee) REQUIRE c.consignee_id IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (co:Country) REQUIRE co.iso_code_2 IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (ip:IndianPort) REQUIRE ip.port_code IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (dp:DestinationPort) REQUIRE dp.port_name IS UNIQUE")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (tm:TimeMonth) REQUIRE tm.year_month IS UNIQUE")

        # Ensure consignee_id column exists
        if 'consignee_id' not in df.columns:
            df['consignee_id'] = df.apply(
                lambda row: self.generate_consignee_id(
                    self.clean_string(row.get('CONSIGNEE NAME')) or '',
                    self.clean_string(row.get('CONSIGNEE ADDRESS')) or ''
                ), axis=1
            )

        total_rows = len(df)
        # Prepare a CSV to record failures for later investigation
        failed_rows_file = "failed_rows.csv"
        with open(failed_rows_file, "w", newline='', encoding='utf-8') as f_failed:
            failed_writer = csv.writer(f_failed)
            failed_writer.writerow(["row_index", "shipment_id", "error", "params_preview"])

        for i in range(0, total_rows, self.batch_size):
            batch = df.iloc[i:i + self.batch_size]
            # Use a transaction per-batch
            with session.begin_transaction() as tx:
                for idx, row in batch.iterrows():
                    # default shipment params
                    try:
                        date_info = self.parse_date(row.get('DATE'))
                        if not date_info:
                            logger.warning(f"Skipping row {idx} — invalid DATE: {row.get('DATE')}")
                            continue

                        invoice_no = self.clean_string(row.get('INVOICE NO')) or ''
                        declaration_no = self.clean_string(row.get('DECLARATION NO')) or ''
                        # stable shipment id: prefer invoice_no, else hashed fallback
                        shipment_id = invoice_no if invoice_no else hashlib.md5(
                            f"{self.clean_string(row.get('IEC'))}_{row.get('DATE')}_{declaration_no}".encode()
                        ).hexdigest()

                        params = {
                            "shipment_id": shipment_id,
                            "invoice_no": invoice_no,
                            "date": date_info['date'],
                            "declaration_no": declaration_no,
                            "year": date_info['year'],
                            "month": date_info['month'],
                            "year_month": date_info['year_month'],
                            "exchange_rate": self.clean_numeric(row.get('EXCHANGE RATE_USD')),
                            "iec": self.clean_string(row.get('IEC')),
                            "hs_code": self.clean_string(row.get('HS CODE')),
                            "goods_description": self.clean_string(row.get('GOODS DESCRIPTION')),
                            "quantity": self.clean_numeric(row.get('QUANTITY')),
                            "unit": self.clean_string(row.get('UNIT')),
                            "unit_price_inr": self.clean_numeric(row.get('UNIT PRICE_INR')),
                            "unit_price_usd": self.clean_numeric(row.get('STD ITEM_RATE_USD', 0)),
                            "fob_inr": self.clean_numeric(row.get('FOB_INR')),
                            "fob_usd": self.clean_numeric(row.get('FOB USD')),
                            "std_quantity": self.clean_numeric(row.get('STD QUANTITY')),
                            "std_unit": self.clean_string(row.get('STD UNIT')),
                            "item_price_inv": self.clean_numeric(row.get('ITEM PRICE_INV')),
                            "currency": self.clean_string(row.get('CURRENCY')),
                            "consignee_id": row.get('consignee_id'),
                            "country_iso": self.clean_string(row.get('country iso_code_2')),
                            "port_code": self.clean_string(row.get('PORT CODE')),
                            "dest_port": self.clean_string(row.get('DESTINATION PORT')),
                        }

                        # 1) Create-or-get Shipment node (always run)
                        tx.run("""
                            MERGE (s:Shipment {shipment_id: $shipment_id})
                            ON CREATE SET
                            s.invoice_no = $invoice_no,
                            s.date = $date,
                            s.declaration_no = $declaration_no,
                            s.year = $year,
                            s.month = $month,
                            s.year_month = $year_month,
                            s.exchange_rate_usd = $exchange_rate
                        """, **params)

                        # 2) Exporter -> Shipment (if IEC provided)
                        if params['iec']:
                            tx.run("""
                                MATCH (e:Exporter {iec: $iec})
                                MATCH (s:Shipment {shipment_id: $shipment_id})
                                MERGE (e)-[:SHIPPED]->(s)
                            """, **params)

                        # 3) Shipment -> Product relationship (if HS code)
                        if params['hs_code']:
                            tx.run("""
                                MATCH (s:Shipment {shipment_id: $shipment_id})
                                MATCH (p:Product {hs_code: $hs_code})
                                MERGE (s)-[c:CONTAINS]->(p)
                                ON CREATE SET
                                    c.goods_description = $goods_description,
                                    c.quantity = $quantity,
                                    c.unit = $unit,
                                    c.unit_price_inr = $unit_price_inr,
                                    c.unit_price_usd = $unit_price_usd,
                                    c.fob_inr = $fob_inr,
                                    c.fob_usd = $fob_usd,
                                    c.std_quantity = $std_quantity,
                                    c.std_unit = $std_unit,
                                    c.item_price_inv = $item_price_inv,
                                    c.currency = $currency
                            """, **params)

                        # 4) Shipment -> Consignee
                        if params['consignee_id']:
                            tx.run("""
                                MATCH (s:Shipment {shipment_id: $shipment_id})
                                MATCH (con:Consignee {consignee_id: $consignee_id})
                                MERGE (s)-[:SENT_TO]->(con)
                            """, **params)

                        # 5) Shipment & Consignee -> Country
                        if params['country_iso']:
                            tx.run("""
                                MATCH (s:Shipment {shipment_id: $shipment_id})
                                MATCH (country:Country {iso_code_2: $country_iso})
                                MERGE (s)-[:EXPORTED_TO]->(country)
                            """, **params)
                            if params['consignee_id']:
                                tx.run("""
                                    MATCH (con:Consignee {consignee_id: $consignee_id})
                                    MATCH (country:Country {iso_code_2: $country_iso})
                                    MERGE (con)-[:LOCATED_IN]->(country)
                                """, **params)

                        # 6) Ports
                        if params['port_code']:
                            tx.run("""
                                MATCH (s:Shipment {shipment_id: $shipment_id})
                                MATCH (ip:IndianPort {port_code: $port_code})
                                MERGE (s)-[:DEPARTED_FROM]->(ip)
                            """, **params)
                        if params['dest_port']:
                            tx.run("""
                                MATCH (s:Shipment {shipment_id: $shipment_id})
                                MATCH (dp:DestinationPort {port_name: $dest_port})
                                MERGE (s)-[:ARRIVED_AT]->(dp)
                            """, **params)

                        # 7) TimeMonth
                        tx.run("""
                            MATCH (s:Shipment {shipment_id: $shipment_id})
                            MATCH (tm:TimeMonth {year_month: $year_month})
                            MERGE (s)-[:OCCURRED_IN]->(tm)
                        """, **params)

                    except Exception as e:
                        # Log failure and write a brief row to failed_rows.csv for later re-run
                        logger.error(f"Error processing row {idx} (shipment_id={shipment_id}): {e}", exc_info=True)
                        with open(failed_rows_file, "a", newline='', encoding='utf-8') as f_failed:
                            failed_writer = csv.writer(f_failed)
                            preview = {
                                "iec": params.get("iec"),
                                "invoice_no": params.get("invoice_no"),
                                "hs_code": params.get("hs_code"),
                                "date": params.get("date")
                            }
                            failed_writer.writerow([idx, shipment_id, str(e), str(preview)])
                        # continue to next row (do not raise)
                        continue

            logger.info(f"Processed {min(i + self.batch_size, total_rows)}/{total_rows} rows "
                        f"({int(min(i + self.batch_size, total_rows) / total_rows * 100)}%)")

        logger.info("Completed shipment creation")
        logger.info(f"Failed rows (if any) written to: {failed_rows_file}")

    
    
    def load_complete_dataset(self, csv_path: str):
        """Complete data loading pipeline"""
        
        logger.info("\n" + "="*80)
        logger.info("STARTING DATA LOAD PROCESS")
        logger.info("="*80 + "\n")
        
        # Load CSV
        df = self.load_data_from_csv(csv_path)
        
        with self.driver.session() as session:
            # Create all node types first
            logger.info("\n--- Creating Node Types ---")
            self.create_time_months(session, df)
            self.create_products(session, df)
            self.create_exporters(session, df)
            self.create_consignees(session, df)
            self.create_countries(session, df)
            self.create_ports(session, df)
            
            # Create shipments and relationships
            logger.info("\n--- Creating Shipments and Relationships ---")
            self.create_shipments_and_relationships(session, df)
        
        logger.info("\n" + "="*80)
        logger.info("✓ DATA LOADING COMPLETED SUCCESSFULLY!")
        logger.info("="*80 + "\n")


def main():
    """Main execution"""
    
    # Configuration - UPDATE THESE
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "shrimpdata123"
    CSV_PATH = "data/shrimp_export_data_30k.csv"
    
    loader = ShrimpDataLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        loader.load_complete_dataset(CSV_PATH)
        
        # Show summary
        print("\n" + "="*80)
        print("DATA LOAD SUMMARY")
        print("="*80)
        print("\nYou can now verify the data in Neo4j Browser:")
        print("  http://localhost:7474")
        print("\nRun these queries to check:")
        print("  1. MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count")
        print("  2. MATCH ()-[r]->() RETURN type(r) as RelType, count(r) as Count")
        print("\nNext step: Run the chatbot!")
        print("  python langchain_chatbot.py")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Error during data loading: {e}")
        raise
    finally:
        loader.close()


if __name__ == "__main__":
    main()