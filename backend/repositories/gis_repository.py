"""GIS repository for spatial data operations."""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import geopandas as gpd
from sqlalchemy.engine import Engine
from sqlalchemy import text

from .base import BaseRepository
from services.layer_config_service import LayerConfigService, LayerConfig
from exceptions import (
    LayerNotFoundError,
    InvalidLayerNameError,
    GISDataProcessingError,
    DatabaseConnectionError,
    SpatialQueryError
)
from utils.db_logger import log_database_operation


@dataclass
class ParcelCriteria:
    """Criteria for parcel queries."""
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    limit: Optional[int] = None
    order_by: str = "area_sqm DESC"


class GISRepository(BaseRepository):
    """Repository for GIS data operations."""
    
    def __init__(self, db_engine: Engine):
        super().__init__(db_engine)
        self.layer_config_service = LayerConfigService(db_engine)
        
    @property
    def layers(self) -> Dict[str, LayerConfig]:
        """Get all available layers from database configuration."""
        return self.layer_config_service.get_all_layers()
    
    def get_available_tables(self) -> List[str]:
        """Get list of available GIS tables."""
        tables = []
        for layer in self.layers.values():
            tables.append(layer.table_name)
        return tables
    
    def get_layer_config(self, layer_name: str) -> LayerConfig:
        """
        Get layer configuration by name.
        
        Args:
            layer_name: Name of the layer
            
        Returns:
            LayerConfig object
            
        Raises:
            InvalidLayerNameError: If layer name is not recognized
        """
        # Normalize layer name
        normalized_name = layer_name.lower().strip()
        
        # Map common names to layer keys
        name_mapping = {
            "działki": "dzialki",
            "dzialki": "dzialki",
            "dzialka": "dzialki",
            "działka": "dzialki",
            "działki_przykładowe": "dzialki",
            "dzialki_przykladowe": "dzialki",
            "przykladowe_dzialki": "dzialki",
            "przykladowe_dzialka": "dzialki",
            "parcels": "dzialki",
            "parcel": "dzialki",
            "budynki": "budynki", 
            "buildings": "budynki",
            "building": "budynki",
            "gpz_wielkopolskie": "gpz_WIELKOPOLSKIE",
            "gpz": "gpz_POLSKA",
            "gpz_110kv": "gpz_POLSKA",
            "gpz_polska": "gpz_POLSKA",
            "wojewodztwa": "wojewodztwa",
            "województwa": "wojewodztwa",
            "natura2000": "natura2000",
            "natura_2000": "natura2000"
        }
        
        layer_key = None
        for pattern, key in name_mapping.items():
            if pattern in normalized_name:
                layer_key = key
                break
        
        if not layer_key or layer_key not in self.layers:
            raise InvalidLayerNameError(
                layer_name=layer_name,
                valid_patterns=list(name_mapping.keys())
            )
        
        return self.layers[layer_key]
    
    def get_layer_data(self, layer_name: str) -> gpd.GeoDataFrame:
        """
        Retrieve complete layer data as GeoDataFrame.
        
        Args:
            layer_name: Name of the layer to retrieve
            
        Returns:
            GeoDataFrame with layer data
            
        Raises:
            LayerNotFoundError: If layer is not found
            GISDataProcessingError: If data processing fails
        """
        layer_config = self.get_layer_config(layer_name)
        table_name = layer_config.table_name
        
        self.logger.info(f"Retrieving layer data: {layer_name} from table {table_name}")
        
        try:
            sql = f'SELECT * FROM "{table_name}";'
            
            with log_database_operation("get_layer_data", table=table_name, layer=layer_name):
                gdf = gpd.read_postgis(
                    sql, 
                    self.db_engine, 
                    geom_col=layer_config.geometry_column
                )
            
            if gdf.empty:
                raise LayerNotFoundError(layer_name=layer_name)
            
            self.logger.info(f"Successfully retrieved {len(gdf)} features from {table_name}")
            
            # Add metadata
            gdf['loaded_layer'] = table_name
            gdf['layer_config'] = layer_config.layer_name
            
            return gdf
            
        except (InvalidLayerNameError, LayerNotFoundError):
            raise
        except Exception as e:
            raise GISDataProcessingError(
                operation=f"reading layer data from {table_name}",
                original_error=e
            )
    
    def find_parcels_by_criteria(self, criteria: ParcelCriteria) -> gpd.GeoDataFrame:
        """
        Find parcels matching specific criteria.
        
        Args:
            criteria: ParcelCriteria object with search parameters
            
        Returns:
            GeoDataFrame with matching parcels
            
        Raises:
            SpatialQueryError: If query execution fails
        """
        layer_config = self.get_layer_config("parcels")
        table_name = layer_config.table_name
        
        # Build WHERE clause
        where_conditions = []
        if criteria.min_area is not None:
            where_conditions.append(f"ST_Area(geometry) >= {criteria.min_area}")
        if criteria.max_area is not None:
            where_conditions.append(f"ST_Area(geometry) <= {criteria.max_area}")
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # Build ORDER BY and LIMIT
        order_clause = f"ORDER BY {criteria.order_by}" if criteria.order_by else ""
        limit_clause = f"LIMIT {criteria.limit}" if criteria.limit else ""
        
        sql = f"""
            SELECT *, ST_Area(geometry) as area_sqm
            FROM "{table_name}"
            {where_clause}
            {order_clause}
            {limit_clause};
        """
        
        try:
            with log_database_operation(
                "find_parcels_by_criteria", 
                table=table_name,
                criteria=criteria.__dict__
            ):
                gdf = gpd.read_postgis(sql, self.db_engine, geom_col='geometry')
            
            if gdf.empty:
                raise LayerNotFoundError(
                    layer_name="parcels matching criteria",
                    available_layers=[table_name]
                )
            
            self.logger.info(f"Found {len(gdf)} parcels matching criteria")
            
            # Add metadata and messages
            gdf['loaded_layer'] = table_name
            
            # Add descriptive messages
            messages = []
            for idx, row in gdf.iterrows():
                parcel_id = row.get(layer_config.id_column, 'Brak ID')
                area_sqm = row.get('area_sqm', 0)
                area_ha = area_sqm / 10000
                
                if criteria.limit == 1:
                    messages.append(f"Największa działka. ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha")
                elif criteria.limit and criteria.limit > 1:
                    messages.append(f"Działka nr {len(messages) + 1}. ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha")
                else:
                    messages.append(f"ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha")
            
            gdf['message'] = messages
            
            return gdf
            
        except (LayerNotFoundError,):
            raise
        except Exception as e:
            raise SpatialQueryError(
                query_type="parcel_criteria_search",
                parameters=criteria.__dict__,
                original_error=e
            )
    
    def find_parcels_near_point(self, point_table: str, radius_meters: float) -> gpd.GeoDataFrame:
        """
        Find parcels within a specified radius of points from another table.
        
        Args:
            point_table: Name of the table containing points
            radius_meters: Search radius in meters
            
        Returns:
            GeoDataFrame with parcels within radius
            
        Raises:
            SpatialQueryError: If spatial query fails
        """
        parcels_config = self.get_layer_config("parcels")
        parcels_table = parcels_config.table_name
        
        sql = f"""
            SELECT p.*, ST_Area(p.geometry) as area_sqm
            FROM "{parcels_table}" p
            WHERE EXISTS (
                SELECT 1
                FROM "{point_table}" g
                WHERE ST_DWithin(p.geometry, g.geom, {radius_meters})
            );
        """
        
        try:
            with log_database_operation(
                "find_parcels_near_point",
                table=parcels_table,
                point_table=point_table,
                radius_meters=radius_meters
            ):
                gdf = gpd.read_postgis(sql, self.db_engine, geom_col='geometry')
            
            if gdf.empty:
                self.logger.info(f"No parcels found within {radius_meters}m of {point_table}")
                # Return empty GeoDataFrame with proper structure
                return gpd.GeoDataFrame(columns=['geometry', 'message'])
            
            self.logger.info(f"Found {len(gdf)} parcels within {radius_meters}m of {point_table}")
            
            # Add metadata and messages
            gdf['loaded_layer'] = parcels_table
            
            messages = []
            for _, row in gdf.iterrows():
                parcel_id = row.get(parcels_config.id_column, 'Brak ID')
                area_sqm = row.get('area_sqm', 0)
                area_ha = area_sqm / 10000
                messages.append(f"ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha")
            
            gdf['message'] = messages
            
            return gdf
            
        except Exception as e:
            raise SpatialQueryError(
                query_type="proximity_search",
                parameters={
                    "point_table": point_table,
                    "radius_meters": radius_meters
                },
                original_error=e
            )
    
    def get_layer_bounds(self, layer_name: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Get bounding box of a layer.
        
        Args:
            layer_name: Name of the layer
            
        Returns:
            Tuple of (minx, miny, maxx, maxy) or None if layer is empty
        """
        try:
            layer_config = self.get_layer_config(layer_name)
            table_name = layer_config.table_name
            
            sql = f"""
                SELECT 
                    ST_XMin(ST_Extent({layer_config.geometry_column})) as minx,
                    ST_YMin(ST_Extent({layer_config.geometry_column})) as miny,
                    ST_XMax(ST_Extent({layer_config.geometry_column})) as maxx,
                    ST_YMax(ST_Extent({layer_config.geometry_column})) as maxy
                FROM "{table_name}";
            """
            
            with self.db_engine.connect() as connection:
                result = connection.execute(text(sql))
                row = result.fetchone()
                
                if row and all(val is not None for val in row):
                    return tuple(row)
                
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get bounds for layer {layer_name}: {e}")
            return None
    
    def find_parcels_without_buildings(self) -> gpd.GeoDataFrame:
        """
        Find parcels that do not contain any buildings within their boundaries.
        
        Returns:
            GeoDataFrame with parcels without buildings
            
        Raises:
            SpatialQueryError: If spatial query fails
        """
        parcels_config = self.get_layer_config("parcels")
        buildings_config = self.get_layer_config("buildings")
        
        parcels_table = parcels_config.table_name
        buildings_table = buildings_config.table_name
        
        sql = f"""
            SELECT p.*, ST_Area(p.geometry) as area_sqm
            FROM "{parcels_table}" p
            WHERE NOT EXISTS (
                SELECT 1
                FROM "{buildings_table}" b
                WHERE ST_Intersects(p.geometry, b.geometry)
            );
        """
        
        try:
            with log_database_operation(
                "find_parcels_without_buildings",
                table=parcels_table,
                buildings_table=buildings_table
            ):
                gdf = gpd.read_postgis(sql, self.db_engine, geom_col='geometry')
            
            if gdf.empty:
                self.logger.info("No parcels without buildings found")
                # Return empty GeoDataFrame with proper structure
                return gpd.GeoDataFrame(columns=['geometry', 'message', 'area_sqm'])
            
            self.logger.info(f"Found {len(gdf)} parcels without buildings")
            
            # Add metadata
            gdf['loaded_layer'] = parcels_table
            
            return gdf
            
        except Exception as e:
            raise SpatialQueryError(
                query_type="parcels_without_buildings_search",
                parameters={
                    "parcels_table": parcels_table,
                    "buildings_table": buildings_table
                },
                original_error=e
            )