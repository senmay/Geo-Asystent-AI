import geopandas as gpd
from langchain.tools import tool
import os
import re

@tool
def get_layer_as_geojson(layer_name: str, data_path: str) -> str:
    """
    Finds a specific GIS layer by its name, reprojects it to WGS 84 (EPSG:4326), 
    and returns it as a GeoJSON string.
    Recognizes layer names like 'parcels', 'buildings', 'parcels_low', 'buildings_low'.
    """
    print(f"Tool 'get_layer_as_geojson' called with raw input: '{layer_name}' and data_path: '{data_path}'")

    if not data_path or not os.path.exists(data_path):
        return "Error: Server-side configuration error. The data directory is not configured correctly."

    normalized_input = layer_name.lower().strip()
    base_layer_name = None
    if "parcel" in normalized_input or "działki" in normalized_input:
        base_layer_name = "parcels"
    elif "building" in normalized_input or "budynki" in normalized_input:
        base_layer_name = "buildings"
    
    if not base_layer_name:
        return f"Error: Could not identify a valid layer name in the input: '{layer_name}'. Please ask for 'parcels' or 'buildings'."

    preferred_path = os.path.join(data_path, f"{base_layer_name}_low.shp")
    fallback_path = os.path.join(data_path, f"{base_layer_name}.shp")
    
    shapefile_path_to_use = None
    if os.path.exists(preferred_path):
        shapefile_path_to_use = preferred_path
    elif os.path.exists(fallback_path):
        shapefile_path_to_use = fallback_path
    else:
        return f"Error: Shapefile for layer '{base_layer_name}' not found in data directory at path {data_path}."

    try:
        print(f"Attempting to read shapefile from: {shapefile_path_to_use}")
        gdf = gpd.read_file(shapefile_path_to_use)
        
        # --- REPROJECTION STEP ---
        # Reproject the data to WGS 84 (EPSG:4326), which is the standard for web maps.
        print(f"Original CRS: {gdf.crs}")
        gdf_reprojected = gdf.to_crs(epsg=4326)
        print(f"Reprojected to CRS: {gdf_reprojected.crs}")
        
        gdf_reprojected['loaded_layer'] = os.path.basename(shapefile_path_to_use)
        return gdf_reprojected.to_json()
    except Exception as e:
        return f"Error during reprojection or file processing: {e}"