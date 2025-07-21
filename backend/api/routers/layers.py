"""Layers API router for direct GIS layer access."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, JSONResponse
from typing import Optional, List

from services import GISService, LayerConfigService
from api.dependencies import get_gis_service, get_layer_config_service
from exceptions import GeoAsystentException, LayerNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["layers"])


@router.get("/layers/config")
async def get_layer_config(
    layer_config_service: LayerConfigService = Depends(get_layer_config_service)
):
    """Get layer configuration."""
    try:
        configs = layer_config_service.get_all_layers()
        
        # Convert to list of dicts for JSON response
        layers = []
        for name, config in configs.items():
            layers.append({
                "layerName": config.layer_name,
                "displayName": config.display_name,
                "tableName": config.table_name,
                "geometryColumn": config.geometry_column,
                "idColumn": config.id_column,
                "description": config.description,
                "style": {
                    "pointColor": config.style.point_color,
                    "pointRadius": config.style.point_radius,
                    "pointOpacity": config.style.point_opacity,
                    "pointFillOpacity": config.style.point_fill_opacity,
                    "lineColor": config.style.line_color,
                    "lineWeight": config.style.line_weight,
                    "lineOpacity": config.style.line_opacity,
                    "lineDashArray": config.style.line_dash_array,
                    "polygonColor": config.style.polygon_color,
                    "polygonWeight": config.style.polygon_weight,
                    "polygonOpacity": config.style.polygon_opacity,
                    "polygonFillColor": config.style.polygon_fill_color,
                    "polygonFillOpacity": config.style.polygon_fill_opacity
                },
                "defaultVisible": config.default_visible,
                "minZoom": config.min_zoom,
                "maxZoom": config.max_zoom,
                "clusterPoints": config.cluster_points,
                "active": config.active
            })
        
        return {"layers": layers}
    except Exception as e:
        logger.error(f"Failed to get layer configuration: {e}")
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


@router.get("/layers/{layer_name}")
async def get_layer(
    layer_name: str,
    gis_service: GISService = Depends(get_gis_service)
):
    """
    Retrieve a specific GIS layer by name as GeoJSON.
    
    This endpoint directly fetches layer data without using the AI agent.
    """
    logger.info(f"Direct layer request: {layer_name}")
    
    try:
        geojson_data = gis_service.get_layer_as_geojson(layer_name)
        return Response(content=geojson_data, media_type="application/json")
    except GeoAsystentException:
        # Custom exceptions are handled by middleware
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving layer: {e}")
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