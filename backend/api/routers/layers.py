"""Layers API router for direct GIS layer access."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, JSONResponse
from typing import Optional, List

from services import GISService
from api.dependencies import get_gis_service
from exceptions import GeoAsystentException, LayerNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["layers"])


@router.get("/layers/{layer_name}")
async def get_layer(
    layer_name: str,
    use_low_resolution: bool = Query(True, description="Whether to use low resolution version if available"),
    gis_service: GISService = Depends(get_gis_service)
):
    """
    Retrieve a specific GIS layer by name as GeoJSON.
    
    This endpoint directly fetches layer data without using the AI agent.
    """
    logger.info(f"Direct layer request: {layer_name} (low_res: {use_low_resolution})")
    
    try:
        geojson_data = gis_service.get_layer_as_geojson(layer_name, use_low_resolution)
        return Response(content=geojson_data, media_type="application/json")
    except GeoAsystentException:
        # Custom exceptions are handled by middleware
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layers")
async def list_layers(gis_service: GISService = Depends(get_gis_service)):
    """
    List all available GIS layers with metadata.
    """
    try:
        layers = gis_service.get_available_layers()
        return {"layers": layers}
    except Exception as e:
        logger.error(f"Failed to list layers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layers/{layer_name}/statistics")
async def get_layer_statistics(layer_name: str, gis_service: GISService = Depends(get_gis_service)):
    """
    Get statistical information about a specific layer.
    """
    try:
        statistics = gis_service.get_layer_statistics(layer_name)
        return statistics
    except LayerNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to get layer statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layers/{layer_name}/validate")
async def validate_layer(layer_name: str, gis_service: GISService = Depends(get_gis_service)):
    """
    Validate the integrity and quality of layer data.
    """
    try:
        validation_results = gis_service.validate_layer_data(layer_name)
        return validation_results
    except LayerNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to validate layer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/parcel-distribution")
async def analyze_parcels(
    thresholds: Optional[List[float]] = Query(None, description="Area thresholds in square meters"),
    gis_service: GISService = Depends(get_gis_service)
):
    """
    Analyze the distribution of parcels by area ranges.
    """
    try:
        distribution = gis_service.analyze_parcel_distribution(thresholds)
        return distribution
    except Exception as e:
        logger.error(f"Failed to analyze parcel distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))