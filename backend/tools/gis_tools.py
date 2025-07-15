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

@tool
def find_largest_parcel(db_engine: Engine) -> str:
    """
    Finds the single largest parcel by area and returns it as a GeoJSON string.
    The result also includes the parcel's ID and its area in square meters.
    """
    print("Tool 'find_largest_parcel' called.")
    
    # We assume the table with parcels is named 'parcels_low'
    table_name = "parcels_low"
    
    # SQL query to find the largest parcel using ST_Area
    # We also calculate the area and select the ID column (assuming it's named 'jpt_kod_je')
    sql = f"""
        SELECT *, ST_Area(geometry) as area_sqm
        FROM "{table_name}"
        ORDER BY area_sqm DESC
        LIMIT 1;
    """
    
    try:
        gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
        if gdf.empty:
            return "Error: Could not find any parcels in the database."
            
        print(f"Found largest parcel with ID: {gdf.iloc[0].get('jpt_kod_je', 'N/A')}")
        
        gdf_reprojected = gdf.to_crs(epsg=4326)
        # Add a custom message to be displayed
        parcel_id = gdf.iloc[0].get('jpt_kod_je', 'Brak ID')
        area = gdf.iloc[0]['area_sqm']
        gdf_reprojected['message'] = f"Największa działka. ID: {parcel_id}, Powierzchnia: {area:.2f} m²"
        
        return gdf_reprojected.to_json()
    except Exception as e:
        return f"Error finding the largest parcel: {e}"

@tool
def find_n_largest_parcels(n: int, db_engine: Engine) -> str:
    """
    Finds the N largest parcels by area and returns them as a GeoJSON string.
    The result also includes each parcel's ID and its area in square meters.
    """
    print(f"Tool 'find_n_largest_parcels' called with n={n}.")
    
    table_name = "parcels_low"
    
    sql = f"""
        SELECT *, ST_Area(geometry) as area_sqm
        FROM "{table_name}"
        ORDER BY area_sqm DESC
        LIMIT {n};
    """
    
    try:
        gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
        if gdf.empty:
            return f"Error: Could not find any parcels in the database."
            
        print(f"Found {len(gdf)} largest parcels.")
        
        gdf_reprojected = gdf.to_crs(epsg=4326)
        
        messages = []
        for index, row in gdf.iterrows():
            parcel_id = row.get('jpt_kod_je', 'Brak ID')
            area = row['area_sqm']
            messages.append(f"Działka nr {index + 1}. ID: {parcel_id}, Powierzchnia: {area:.2f} m²")
        
        gdf_reprojected['message'] = messages
        
        return gdf_reprojected.to_json()
    except Exception as e:
        return f"Error finding the {n} largest parcels: {e}"

@tool
def find_parcels_above_area(min_area: float, db_engine: Engine) -> str:
    """
    Finds all parcels with an area greater than a specified minimum area and returns them as a GeoJSON string.
    The result also includes each parcel's ID and its area in square meters.
    """
    print(f"Tool 'find_parcels_above_area' called with min_area={min_area}.")
    
    table_name = "parcels_low"
    
    sql = f"""
        SELECT *, ST_Area(geometry) as area_sqm
        FROM "{table_name}"
        WHERE ST_Area(geometry) > {min_area};
    """
    
    try:
        gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
        if gdf.empty:
            return f"Error: Could not find any parcels with an area greater than {min_area} m²."
            
        print(f"Found {len(gdf)} parcels with area above {min_area} m².")
        
        gdf_reprojected = gdf.to_crs(epsg=4326)
        
        messages = []
        for index, row in gdf.iterrows():
            parcel_id = row.get('jpt_kod_je', 'Brak ID')
            area = row['area_sqm']
            messages.append(f"ID: {parcel_id}, Powierzchnia: {area:.2f} m²")
            
        gdf_reprojected['message'] = messages
        
        return gdf_reprojected.to_json()
    except Exception as e:
        return f"Error finding parcels above {min_area} m²: {e}"
