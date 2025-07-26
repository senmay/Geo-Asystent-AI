"""
Result processing utilities for GIS operations.

This module consolidates common result processing functions to eliminate code duplication
across services and tools.
"""

from typing import Tuple, Optional
import geopandas as gpd


def limit_results_for_display(gdf: gpd.GeoDataFrame, max_display: int = 5, item_type: str = "działka") -> Tuple[gpd.GeoDataFrame, Optional[str]]:
    """
    Limit results for chat display and add summary message.
    
    Args:
        gdf: GeoDataFrame with results
        max_display: Maximum number of items to show in chat
        item_type: Type of item (działka, budynek, etc.)
    
    Returns:
        Tuple of (limited_gdf, summary_message)
    """
    total_count = len(gdf)
    
    if total_count <= max_display:
        return gdf, None
    
    # Limit to first max_display results
    limited_gdf = gdf.head(max_display).copy()
    
    # Create summary message
    remaining = total_count - max_display
    if item_type == "działka":
        summary = f"Wyświetlono {max_display} z {total_count} działek. Pozostałe {remaining} działek dostępne w PDF."
    elif item_type == "budynek":
        summary = f"Wyświetlono {max_display} z {total_count} budynków. Pozostałe {remaining} budynków dostępne w PDF."
    else:
        summary = f"Wyświetlono {max_display} z {total_count} wyników. Pozostałe {remaining} wyników dostępne w PDF."
    
    return limited_gdf, summary


def create_parcel_message(parcel_id: str, area_sqm: float, message_type: str = "standard") -> str:
    """
    Create a standardized message for parcel display.
    
    Args:
        parcel_id: ID of the parcel
        area_sqm: Area in square meters
        message_type: Type of message ("standard", "largest", "numbered", "unbuilt")
    
    Returns:
        Formatted message string
    """
    area_ha = area_sqm / 10000
    
    if message_type == "largest":
        return f"Największa działka. ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha"
    elif message_type == "unbuilt":
        return f"Niezabudowana działka. ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha"
    else:  # standard
        return f"ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha"


def create_numbered_parcel_message(index: int, parcel_id: str, area_sqm: float) -> str:
    """
    Create a numbered parcel message for lists.
    
    Args:
        index: 1-based index number
        parcel_id: ID of the parcel
        area_sqm: Area in square meters
    
    Returns:
        Formatted numbered message string
    """
    area_ha = area_sqm / 10000
    return f"Działka nr {index}. ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha"


def add_parcel_messages(gdf: gpd.GeoDataFrame, message_type: str = "standard") -> gpd.GeoDataFrame:
    """
    Add standardized messages to a GeoDataFrame with parcel data.
    
    Args:
        gdf: GeoDataFrame with parcel data
        message_type: Type of message to create ("standard", "largest", "numbered", "unbuilt")
    
    Returns:
        GeoDataFrame with 'message' column added
    """
    if gdf.empty:
        return gdf
    
    messages = []
    for index, row in gdf.iterrows():
        parcel_id = row.get('ID_DZIALKI', 'Brak ID')
        area_sqm = row.get('area_sqm', 0)
        
        if message_type == "numbered":
            message = create_numbered_parcel_message(len(messages) + 1, parcel_id, area_sqm)
        else:
            message = create_parcel_message(parcel_id, area_sqm, message_type)
        
        messages.append(message)
    
    gdf_copy = gdf.copy()
    gdf_copy['message'] = messages
    return gdf_copy


def add_simple_id_messages(gdf: gpd.GeoDataFrame, id_column: str) -> gpd.GeoDataFrame:
    """
    Add simple ID-based messages to a GeoDataFrame.
    
    Args:
        gdf: GeoDataFrame with data
        id_column: Name of the ID column
    
    Returns:
        GeoDataFrame with 'message' column added
    """
    if gdf.empty or id_column not in gdf.columns:
        return gdf
    
    gdf_copy = gdf.copy()
    gdf_copy['message'] = gdf_copy[id_column].apply(lambda x: f"ID: {x}")
    return gdf_copy


def convert_to_geojson(gdf: gpd.GeoDataFrame, target_crs: str = "EPSG:4326") -> str:
    """
    Convert GeoDataFrame to GeoJSON string with proper CRS handling.
    
    Args:
        gdf: GeoDataFrame to convert
        target_crs: Target coordinate reference system (default: WGS84)
    
    Returns:
        GeoJSON string
    """
    if gdf.empty:
        return '{"type": "FeatureCollection", "features": []}'
    
    # Reproject to target CRS if needed
    if gdf.crs is not None and str(gdf.crs) != target_crs:
        gdf_reprojected = gdf.to_crs(target_crs)
    else:
        gdf_reprojected = gdf
    
    return gdf_reprojected.to_json()