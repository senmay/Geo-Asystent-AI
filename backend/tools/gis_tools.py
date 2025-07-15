import geopandas as gpd
from langchain.tools import tool
import os
from sqlalchemy.engine import Engine

@tool
def get_layer_as_geojson(layer_name: str, db_engine: Engine) -> str:
    """
    Retrieves a GIS layer from the PostGIS database using a provided database engine,
    reprojects it to WGS 84 (EPSG:4326), and returns it as a GeoJSON string.
    Recognizes layer names like 'parcels', 'buildings', 'parcels_low', 'buildings_low'.
    """
    print(f"Tool 'get_layer_as_geojson' called with layer_name: '{layer_name}'")

    normalized_input = layer_name.lower().strip()
    base_layer_name = None
    if "parcel" in normalized_input or "działki" in normalized_input:
        base_layer_name = "parcels"
    elif "building" in normalized_input or "budynki" in normalized_input:
        base_layer_name = "buildings"
    
    if not base_layer_name:
        return f"Error: Could not identify a valid layer name in the input: '{layer_name}'. Please ask for 'parcels' or 'buildings'."

    table_to_use = f"{base_layer_name}_low"
    print(f"Attempting to query table: '{table_to_use}'")

    try:
        sql = f'SELECT * FROM "{table_to_use}";'
        gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
        
        print(f"Successfully read {len(gdf)} features from table '{table_to_use}'.")
        
        gdf_reprojected = gdf.to_crs(epsg=4326)
        gdf_reprojected['loaded_layer'] = table_to_use
        return gdf_reprojected.to_json()
        
    except Exception as e:
        print(f"Could not read from '{table_to_use}', trying full resolution. Error: {e}")
        table_to_use = base_layer_name
        try:
            sql = f'SELECT * FROM "{table_to_use}";'
            gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
            print(f"Successfully read {len(gdf)} features from fallback table '{table_to_use}'.")
            
            gdf_reprojected = gdf.to_crs(epsg=4326)
            gdf_reprojected['loaded_layer'] = table_to_use
            return gdf_reprojected.to_json()
        except Exception as final_e:
            return f"Error processing data from database: {final_e}"