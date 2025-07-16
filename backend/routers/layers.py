
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.engine import Engine
from database import get_db_engine
from tools.gis_tools import get_layer_as_geojson

router = APIRouter()

@router.get("/api/v1/layers/{layer_name}", response_class=Response)
def get_layer(layer_name: str, db_engine: Engine = Depends(get_db_engine)):
    """
    Retrieves a specific GIS layer by name as a GeoJSON.
    This endpoint directly fetches data without using the AI agent.
    """
    # We can reuse the core logic from the existing tool
    # The tool function needs to be called with the correct arguments.
    # Since the tool itself is decorated with @tool, we call its wrapped function.
    geojson_data = get_layer_as_geojson.func(layer_name=layer_name, db_engine=db_engine)

    if geojson_data.startswith("Error:"):
        raise HTTPException(status_code=404, detail=geojson_data)
    
    # Return the GeoJSON string with the correct media type
    return Response(content=geojson_data, media_type="application/json")
