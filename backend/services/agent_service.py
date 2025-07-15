from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from tools.gis_tools import get_layer_as_geojson
from database import engine  # Import the configured database engine

# --- LLM Configuration ---
llm = ChatGroq(model_name="llama3-8b-8192", temperature=0)

# --- Pydantic model for structured output ---
class QueryRoute(BaseModel):
    intent: str = Field(description="The user's intent. Must be one of: 'get_gis_data' or 'chat'.")
    layer_name: str | None = Field(description="If intent is 'get_gis_data', the name of the layer to retrieve. E.g., 'parcels' or 'buildings'. Otherwise null.")

# --- Intent Classification Logic ---
parser = JsonOutputParser(pydantic_object=QueryRoute)

prompt = PromptTemplate(
    template="""
You are an expert query router. Your task is to analyze the user's query and determine their intent.
Respond with a JSON object containing the intent and any relevant parameters.

The user can have two intents:
1. 'get_gis_data': The user wants to see a GIS layer on the map. Look for layer names like 'parcels', 'działki', 'buildings', 'budynki'.
2. 'chat': The user is making small talk, asking a general question, or saying hello.

User query:
{query}

Format instructions:
{format_instructions}
""",
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

routing_chain = prompt | llm | parser
chat_prompt = PromptTemplate.from_template("You are a helpful assistant. Answer the following question concisely.\nQuestion: {query}")
chat_chain = chat_prompt | llm

def process_query(query: str) -> dict:
    """
    Processes the user query by first routing it to the correct logic (GIS or chat).
    """
    print(f"Processing query: '{query}'")
    
    try:
        route = routing_chain.invoke({"query": query})
        intent = route.get("intent")
        print(f"Routed to intent: '{intent}'")

        if intent == 'get_gis_data':
            layer_name = route.get("layer_name")
            if not layer_name:
                return {"type": "text", "data": "Widzę, że prosisz o dane, ale nie sprecyzowałeś które. Spróbuj 'pokaż działki' lub 'pokaż budynki'."}
            
            # Pass the database engine to the tool
            tool_input = {"layer_name": layer_name, "db_engine": engine}
            geojson_data = get_layer_as_geojson.invoke(tool_input)
            
            if "Error:" in geojson_data:
                 return {"type": "text", "data": geojson_data}
            else:
                return {"type": "geojson", "data": geojson_data}
        
        else: # Intent is 'chat'
            response = chat_chain.invoke({"query": query})
            return {"type": "text", "data": response.content}

    except Exception as e:
        print(f"An error occurred during query processing: {e}")
        try:
            response = chat_chain.invoke({"query": query})
            return {"type": "text", "data": response.content}
        except Exception as final_e:
            print(f"Final fallback failed: {final_e}")
            return {"type": "text", "data": "Przepraszam, mam problem z przetworzeniem Twojego zapytania."}
