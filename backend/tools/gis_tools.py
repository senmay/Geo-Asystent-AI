import geopandas as gpd
from langchain.tools import tool
import os
from sqlalchemy.engine import Engine
import logging

from exceptions import (
    LayerNotFoundError,
    InvalidLayerNameError,
    GISDataProcessingError,
    DatabaseConnectionError,
    SpatialQueryError
)
from utils.db_logger import log_database_operation

logger = logging.getLogger(__name__)

@tool
def get_layer_as_geojson(layer_name: str, db_engine: Engine) -> str:
    """
    Retrieves a GIS layer from the PostGIS database using a provided database engine,
    reprojects it to WGS 84 (EPSG:4326), and returns it as a GeoJSON string.
    Recognizes layer names like 'parcels', 'buildings', 'parcels_low', 'buildings_low'.
    """
    logger.info(f"Retrieving layer: '{layer_name}'")

    normalized_input = layer_name.lower().strip()
    base_layer_name = None
    id_column = None
    
    if "parcel" in normalized_input or "działki" in normalized_input:
        base_layer_name = "parcels"
        id_column = "ID_DZIALKI"
    elif "building" in normalized_input or "budynki" in normalized_input:
        base_layer_name = "buildings"
        id_column = "ID_BUDYNKU"
    elif "gpz" in normalized_input:
        base_layer_name = "gpz_110kv"
        id_column = "id"
    
    if not base_layer_name:
        raise InvalidLayerNameError(
            layer_name=layer_name,
            valid_patterns=["działki", "budynki", "gpz"]
        )

    # GPZ layer doesn't have a _low version
    if base_layer_name == "gpz_110kv":
        table_to_use = base_layer_name
    else:
        table_to_use = f"{base_layer_name}_low"
    
    logger.debug(f"Querying table: '{table_to_use}'")

    try:
        sql = f'SELECT * FROM "{table_to_use}";'
        
        # Handle different geometry column names
        geom_col = 'geom' if base_layer_name == "gpz_110kv" else 'geometry'
        
        try:
            gdf = gpd.read_postgis(sql, db_engine, geom_col=geom_col)
        except Exception as e:
            raise DatabaseConnectionError(
                operation=f"reading from table '{table_to_use}'",
                original_error=e
            )
        
        if gdf.empty:
            raise LayerNotFoundError(layer_name=layer_name)
        
        logger.info(f"Successfully read {len(gdf)} features from table '{table_to_use}'")
        
        try:
            gdf_reprojected = gdf.to_crs(epsg=4326)
            gdf_reprojected['loaded_layer'] = table_to_use
            
            # Add a message with the ID
            if id_column and id_column in gdf.columns:
                gdf_reprojected['message'] = gdf_reprojected[id_column].apply(lambda x: f"ID: {x}")
            
            return gdf_reprojected.to_json()
            
        except Exception as e:
            raise GISDataProcessingError(
                operation="coordinate transformation and GeoJSON conversion",
                original_error=e
            )
        
    except (InvalidLayerNameError, LayerNotFoundError, DatabaseConnectionError, GISDataProcessingError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Try fallback to full resolution table
        logger.warning(f"Failed to read from '{table_to_use}', trying full resolution table")
        table_to_use = base_layer_name
        
        try:
            sql = f'SELECT * FROM "{table_to_use}";'
            gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
            
            if gdf.empty:
                raise LayerNotFoundError(layer_name=layer_name)
            
            logger.info(f"Successfully read {len(gdf)} features from fallback table '{table_to_use}'")
            
            gdf_reprojected = gdf.to_crs(epsg=4326)
            gdf_reprojected['loaded_layer'] = table_to_use
            
            if id_column and id_column in gdf.columns:
                gdf_reprojected['message'] = gdf_reprojected[id_column].apply(lambda x: f"ID: {x}")

            return gdf_reprojected.to_json()
            
        except Exception as final_e:
            raise GISDataProcessingError(
                operation=f"reading from fallback table '{table_to_use}'",
                original_error=final_e
            )

@tool
def find_largest_parcel(db_engine: Engine) -> str:
    """
    Finds the single largest parcel by area and returns it as a GeoJSON string.
    The result also includes the parcel's ID and its area in square meters.
    """
    logger.info("Finding largest parcel")
    
    table_name = "parcels_low"
    
    sql = f"""
        SELECT *, ST_Area(geometry) as area_sqm
        FROM "{table_name}"
        ORDER BY area_sqm DESC
        LIMIT 1;
    """
    
    try:
        with log_database_operation("find_largest_parcel", table=table_name):
            gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
            
        if gdf.empty:
            raise LayerNotFoundError(layer_name="parcels", available_layers=["parcels_low", "parcels"])
            
        logger.info(f"Found largest parcel with ID: {gdf.iloc[0].get('ID_DZIALKI', 'N/A')}")
        
        try:
            gdf_reprojected = gdf.to_crs(epsg=4326)
            parcel_id = gdf.iloc[0].get('ID_DZIALKI', 'Brak ID')
            area_sqm = gdf.iloc[0]['area_sqm']
            area_ha = area_sqm / 10000
            gdf_reprojected['message'] = f"Największa działka. ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha"
            
            return gdf_reprojected.to_json()
            
        except Exception as e:
            raise GISDataProcessingError(
                operation="coordinate transformation and GeoJSON conversion for largest parcel",
                original_error=e
            )
            
    except (LayerNotFoundError, GISDataProcessingError):
        raise
    except Exception as e:
        raise DatabaseConnectionError(
            operation=f"finding largest parcel in table '{table_name}'",
            original_error=e
        )

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
            parcel_id = row.get('ID_DZIALKI', 'Brak ID')
            area_sqm = row['area_sqm']
            area_ha = area_sqm / 10000
            messages.append(f"Działka nr {index + 1}. ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha")
        
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
            parcel_id = row.get('ID_DZIALKI', 'Brak ID')
            area_sqm = row['area_sqm']
            area_ha = area_sqm / 10000
            messages.append(f"ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha")
            
        gdf_reprojected['message'] = messages
        
        return gdf_reprojected.to_json()
    except Exception as e:
        return f"Error finding parcels above {min_area} m²: {e}"

@tool
def find_parcels_near_gpz(radius_meters: int, db_engine: Engine) -> str:
    """
    Finds all parcels within a specified radius of any GPZ point.
    The result includes each parcel's ID and its area.
    The radius is specified in meters.
    """
    print(f"Tool 'find_parcels_near_gpz' called with radius_meters={radius_meters}.")

    parcels_table = "parcels_low"
    gpz_table = "gpz_110kv"

    # This SQL query uses a subquery with ST_DWithin for efficient spatial filtering.
    # It finds all parcels where the distance to any GPZ is within the specified radius.
    # NOTE: This assumes both layers are in the same CRS in the database.
    # If not, a transform would be needed, but ST_DWithin is much faster on projected CRS.
    sql = f"""
        SELECT p.*, ST_Area(p.geometry) as area_sqm
        FROM "{parcels_table}" p
        WHERE EXISTS (
            SELECT 1
            FROM "{gpz_table}" g
            WHERE ST_DWithin(p.geometry, g.geom, {radius_meters})
        );
    """

    try:
        gdf = gpd.read_postgis(sql, db_engine, geom_col='geometry')
        if gdf.empty:
            logger.info(f"No parcels found within {radius_meters}m of a GPZ, returning empty GeoJSON.")
            return '{"type": "FeatureCollection", "features": []}'

        logger.info(f"Found {len(gdf)} parcels within {radius_meters}m of a GPZ.")

        gdf_reprojected = gdf.to_crs(epsg=4326)

        messages = []
        for index, row in gdf.iterrows():
            parcel_id = row.get('ID_DZIALKI', 'Brak ID')
            area_sqm = row['area_sqm']
            area_ha = area_sqm / 10000
            messages.append(f"ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha")

        gdf_reprojected['message'] = messages

        return gdf_reprojected.to_json()
    except Exception as e:
        logger.error(f"Error in find_parcels_near_gpz tool: {e}", exc_info=True)
        # Re-raise the exception to be handled by the agent/caller,
        # which should result in a proper JSON error response.
        raise
