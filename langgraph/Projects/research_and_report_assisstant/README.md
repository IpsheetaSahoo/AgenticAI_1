
🧠 LangGraph Agentic Workflow
This project demonstrates a modular multi-agent architecture using LangGraph in a Jupyter Notebook environment. It supports intelligent routing for research and reporting tasks using a Supervisor-Agent model.


Notebook Cells:
1. Imports & Setup
2. Agent Node Definitions:
   - supervisor
   - research_agent
   - medical_research_agent
   - financial_research_agent
   - report_agent
   - summarization_agent
   - documentation_agent

3. LangGraph Wiring:
   - Define edges and routing
   - Compile full graph

4. Test Cases
   - Sample queries covering all paths
  

---

## 💪 Agents & Responsibilities

### Supervisor Node

Routes user intent to one of:

- `research_agent`
- `report_agent`
- `END` (irrelevant or complete queries)

### Research Agent

Further routes:

- `medical_research_agent` (e.g. health queries)
- `financial_research_agent` (e.g. GDP, inflation)
- or returns to Supervisor with response

### Report Agent

Further routes:

- `summarization_agent` (e.g. meeting notes)
- `documentation_agent` (e.g. report generation)
- or returns to Supervisor with response

### Leaf Nodes

- Fetch or generate content and return to parent
- All terminal nodes currently route **back to their supervisor**

---

## 📝 Sample Queries & Routing

| Query Example                                 | Final Agent                |
| --------------------------------------------- | -------------------------- |
| "What is the projected GDP of China in 2025?" | `financial_research_agent` |
| "Summarize our Q3 meeting transcript."        | `summarization_agent`      |
| "Create a performance report for last month." | `documentation_agent`      |
| "What are good productivity tools?"           | `END`                      |

---

## 🚀 To Run

Inside the notebook:

```python
from langchain.schema import HumanMessage

state = {"messages": [HumanMessage(content="What is the projected GDP of China in 2025?")]}
result = graph.invoke(state)
