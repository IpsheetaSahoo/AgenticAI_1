"""
graph/nodes/start_router_node.py

This node uses an LLM to classify the user's query intent and routes the workflow accordingly.
Possible intents: 'weather', 'hotels', 'attractions', 'itinerary'
"""
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableMap
from langchain_core.output_parsers import StrOutputParser
from utils.schemas import TravelPlannerState


def create_start_router_node():
    """
    Creates a node that determines the user’s intent and updates the LangGraph state.
    """

    prompt = ChatPromptTemplate.from_template("""
    You are a travel planner AI. A user is asking something related to travel.
    Classify their query into one of these categories:
    - "weather": if the user asks about climate or forecast
    - "hotels": if the user asks about accommodations
    - "attractions": if the user wants to know places to visit
    - "itinerary": if the user wants a full travel plan with cost and daily plan

    Return only one word as output: weather, hotels, attractions, or itinerary.

    User query: {query}
    """)

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    def router(state):
        intent = (
            prompt
            | model
            | StrOutputParser()
        ).invoke({"query": state.user_input.raw_query})
        return state.model_copy(update={
            "user_input": state.user_input.model_copy(update={"query_intent": intent.strip().lower()})
        })
    return router
