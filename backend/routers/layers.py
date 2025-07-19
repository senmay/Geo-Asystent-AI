
"""API router for GIS layer operations."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.engine import Engine
from typing import Dict, Any

from config.database import get_db_engine
from services import GISService
from models.schemas import LayerInfoResponse, LayerStatisticsResponse

router = APIRouter()


def get_gis_service(db_engine: Engine = Depends(get_db_engine)) -> GISService:
    """Dependency to get GIS service instance."""
    return GISService(db_engine)


@router.get("/api/v1/layers/{layer_name}", response_class=Response)
def get_layer(layer_name: str, gis_service: GISService = Depends(get_gis_service)):
    """
    Retrieves a specific GIS layer by name as a GeoJSON.
    This endpoint uses the GIS service layer for data retrieval.
    """
    geojson_data = gis_service.get_layer_as_geojson(layer_name)
    
    # Return the GeoJSON string with the correct media type
    return Response(content=geojson_data, media_type="application/json")


@router.get("/api/v1/layers/{layer_name}/info")
def get_layer_info(layer_name: str, gis_service: GISService = Depends(get_gis_service)) -> Dict[str, Any]:
    """
    Get information about a specific GIS layer.
    """
    return gis_service.get_layer_info(layer_name)


@router.get("/api/v1/layers/{layer_name}/statistics")
def get_layer_statistics(layer_name: str, gis_service: GISService = Depends(get_gis_service)) -> Dict[str, Any]:
    """
    Get statistical information about a specific GIS layer.
    """
    return gis_service.get_layer_statistics(layer_name)


@router.get("/api/v1/layers/{layer_name}/validate")
def validate_layer(layer_name: str, gis_service: GISService = Depends(get_gis_service)) -> Dict[str, Any]:
    """
    Validate the integrity and quality of a GIS layer.
    """
    return gis_service.validate_layer_data(layer_name)


@router.get("/api/v1/layers")
def get_available_layers(gis_service: GISService = Depends(get_gis_service)) -> Dict[str, Dict[str, Any]]:
    """
    Get information about all available GIS layers.
    """
    return gis_service.get_available_layers()
