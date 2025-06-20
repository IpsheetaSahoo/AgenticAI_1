# ⚖️ Legal Research Agent (LangGraph + LangChain)

A decision-aware, modular legal research assistant built using **LangGraph**, **LangChain**, and **Streamlit**.  
This agent intelligently routes user queries to the best processing path (LLM, RAG, or Web) and validates the final output using LLM before displaying it.

---

## 🧠 Architecture

![image](https://github.com/user-attachments/assets/c51d066f-9ae1-4d94-a21f-27ebf2ae7d7b)

💻 **How It Works**

1. Supervisor Node: Validates query intent (legal, clear, actionable)

2. Router Node: Uses LLM to route to:

      llm_agent: for general legal questions

      rag_agent: for doc-based answers (PDF)

      web_crawler: for real-time legal info

3. Validator Node: Checks factual accuracy, relevance, and jurisdiction

4. Finalizer: Delivers the final response or flags retry

⚙️** Run Locally**

📦 Setup

git clone https://github.com/IpsheetaSahoo/AgenticAI_1.git

cd langgraph

cd Projects

cd legal_research_agent

pip install -r requirements.txt

▶️ Run the Agent

streamlit run app.py

**✨ Sample Queries**

✅ Valid Legal (LLM/RAG/Web)

What is the meaning of natural justice?

What is the role of JCC in the 2018 MoU?

What was the Supreme Court’s verdict on electoral bonds?

❌ Invalid/Non-Legal

Plan a 5-day vacation to Thailand

What’s the best laptop under ₹50,000?

📸 UI Preview



![image](https://github.com/user-attachments/assets/5ff6682a-4c06-4386-913e-61ac25d716bf)



