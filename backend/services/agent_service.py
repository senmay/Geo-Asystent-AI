from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Literal, Union

from tools.gis_tools import get_layer_as_geojson, find_largest_parcel, find_n_largest_parcels, find_parcels_above_area
from database import engine

# --- LLM Configuration ---
llm = ChatGroq(model_name="llama3-8b-8192", temperature=0)

# --- Pydantic Models for each Intent ---
class GetGisData(BaseModel):
    """Użytkownik chce zobaczyć całą warstwę GIS na mapie."""
    intent: Literal['get_gis_data'] = "get_gis_data"
    layer_name: str = Field(description="Nazwa warstwy do pobrania, np. 'działki' lub 'budynki'.")

class FindLargestParcel(BaseModel):
    """Użytkownik chce znaleźć pojedynczą największą działkę."""
    intent: Literal['find_largest_parcel'] = "find_largest_parcel"

class FindNLargestParcels(BaseModel):
    """Użytkownik chce znaleźć określoną liczbę największych działek."""
    intent: Literal['find_n_largest_parcels'] = "find_n_largest_parcels"
    n: int = Field(description="Liczba największych działek do znalezienia.")

class FindParcelsAboveArea(BaseModel):
    """Użytkownik chce znaleźć wszystkie działki o powierzchni powyżej określonego progu."""
    intent: Literal['find_parcels_above_area'] = "find_parcels_above_area"
    min_area: float = Field(description="Minimalna powierzchnia w metrach kwadratowych.")

class Chat(BaseModel):
    """Użytkownik prowadzi luźną rozmowę, zadaje ogólne pytanie lub jego intencja jest niejasna."""
    intent: Literal['chat'] = "chat"

# --- Union of all possible routes ---
class Route(BaseModel):
    route: Union[GetGisData, FindLargestParcel, FindNLargestParcels, FindParcelsAboveArea, Chat]

# --- Intent Classification Logic ---
parser = JsonOutputParser(pydantic_object=Route)

prompt = PromptTemplate(
    template="""Jesteś precyzyjnym i rygorystycznym routerem zapytań w języku polskim. Twoim jedynym zadaniem jest zaklasyfikowanie zapytania użytkownika do jednego z podanych schematów Pydantic i zwrócenie wyniku w formacie JSON. Musisz bezwzględnie przestrzegać poniższych reguł:

1.  **Analiza i mapowanie:**
    *   Jeśli użytkownik prosi o wizualizację warstwy (np. "pokaż działki", "wczytaj budynki"), użyj `GetGisData` i ustaw `layer_name`.
    *   Jeśli użytkownik pyta o największą działkę (np. "jaka jest największa działka?"), użyj `FindLargestParcel`.
    *   Jeśli użytkownik prosi o `n` największych działek (np. "pokaż 10 największych działek"), użyj `FindNLargestParcels` i ustaw `n`.
    *   Jeśli użytkownik prosi o działki powyżej pewnej powierzchni (np. "działki powyżej 100 mkw"), użyj `FindParcelsAboveArea` i ustaw `min_area`.
    *   Dla każdej innej interakcji (np. "cześć", "pomoc"), użyj `Chat`.

2.  **Ekstrakcja parametrów:**
    *   Precyzyjnie wyekstrahuj wartości liczbowe (`n`, `min_area`) i tekstowe (`layer_name`) z zapytania.

3.  **Format wyjściowy:**
    *   Zawsze zwracaj odpowiedź jako obiekt JSON zgodny ze schematem. Nie dodawaj żadnych dodatkowych komentarzy ani wyjaśnień.

PRZYKŁADY:
-   `Zapytanie: "pokaż mi 5 największych działek" -> JSON: {{"route": {{"intent": "find_n_largest_parcels", "n": 5}}}}`
-   `Zapytanie: "działki większe niż 250m2" -> JSON: {{"route": {{"intent": "find_parcels_above_area", "min_area": 250}}}}`
-   `Zapytanie: "pokaż warstwę budynków" -> JSON: {{"route": {{"intent": "get_gis_data", "layer_name": "budynki"}}}}`
-   `Zapytanie: "dzień dobry" -> JSON: {{"route": {{"intent": "chat"}}}}`

ZAPYTANIE UŻYTKOWNIKA:
{query}

SCHEMAT:
{format_instructions}
""",
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

routing_chain = prompt | llm | parser
chat_prompt = PromptTemplate.from_template(
    """Jesteś pomocnym asystentem. Odpowiedz na poniższe pytanie zwięźle i uprzejmie w języku polskim. Jeśli pytanie nie dotyczy GIS, staraj się udzielić ogólnej, sensownej odpowiedzi. Jeśli nie znasz odpowiedzi, powiedz, że nie wiesz.

Question: {query}"""
)
chat_chain = chat_prompt | llm

def process_query(query: str) -> dict:
    """
    Processes the user query by first routing it to the correct logic.
    """
    print(f"Processing query: '{query}'")
    
    try:
        response = routing_chain.invoke({"query": query})
        route_details = response.get('route', {})
        intent = route_details.get("intent")
        print(f"Routed to intent: '{intent}' with details: {route_details}")

        if intent == 'get_gis_data':
            tool_input = {"layer_name": route_details['layer_name'], "db_engine": engine}
            geojson_data = get_layer_as_geojson.invoke(tool_input)
        
        elif intent == 'find_largest_parcel':
            tool_input = {"db_engine": engine}
            geojson_data = find_largest_parcel.invoke(tool_input)

        elif intent == 'find_n_largest_parcels':
            tool_input = {"n": route_details['n'], "db_engine": engine}
            geojson_data = find_n_largest_parcels.invoke(tool_input)

        elif intent == 'find_parcels_above_area':
            tool_input = {"min_area": route_details['min_area'], "db_engine": engine}
            geojson_data = find_parcels_above_area.invoke(tool_input)

        else: # Intent is 'chat' or fallback
            response = chat_chain.invoke({"query": query})
            return {"type": "text", "data": response.content}

        # Common return logic for GIS tools
        if "Error:" in geojson_data:
            return {"type": "text", "data": geojson_data, "intent": intent}
        else:
            return {"type": "geojson", "data": geojson_data, "intent": intent}

    except Exception as e:
        print(f"An error occurred during query processing: {e}")
        return {"type": "text", "data": """Przepraszam, nie rozumiem Twojego zapytania. Jestem asystentem GIS i mogę:
- Wyświetlić warstwy GIS (np. "pokaż działki", "wczytaj budynki").
- Znaleźć największą działkę (np. "jaka jest największa działka").
- Znaleźć N największych działek (np. "pokaż 10 największych działek").
- Znaleźć działki o powierzchni większej niż X (np. "działki powyżej 100m2").
Spróbuj sformułować zapytanie w jeden z tych sposobów.""", "intent": "error"}
