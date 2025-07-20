"""GIS service layer for business logic."""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
import geopandas as gpd
from sqlalchemy.engine import Engine

from repositories import GISRepository
from models.domain import ParcelCriteria, QueryResult, GISOperationResult
from exceptions import GeoAsystentException, GISDataProcessingError, SpatialQueryError
from utils.db_logger import log_gis_operation

logger = logging.getLogger(__name__)


class GISService:
    """Service layer for GIS operations."""
    
    def __init__(self, db_engine: Engine):
        """
        Initialize GIS service with database engine.
        
        Args:
            db_engine: SQLAlchemy database engine
        """
        self.repository = GISRepository(db_engine)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @log_gis_operation("layer_retrieval")
    def get_layer_as_geojson(self, layer_name: str, use_low_resolution: bool = True) -> str:
        """
        Get layer data as GeoJSON string.
        
        Args:
            layer_name: Name of the layer to retrieve
            use_low_resolution: Whether to use low resolution version
            
        Returns:
            GeoJSON string
            
        Raises:
            GeoAsystentException: If operation fails
        """
        self.logger.info(f"Retrieving layer as GeoJSON: {layer_name}")
        
        try:
            gdf = self.repository.get_layer_data(layer_name, use_low_resolution)
            
            # Reproject to WGS84 for web display
            gdf_reprojected = gdf.to_crs(epsg=4326)
            
            # Add ID messages if ID column exists
            layer_config = self.repository.get_layer_config(layer_name)
            if layer_config.id_column in gdf_reprojected.columns:
                gdf_reprojected['message'] = gdf_reprojected[layer_config.id_column].apply(
                    lambda x: f"ID: {x}"
                )
            
            self.logger.info(f"Successfully converted {len(gdf_reprojected)} features to GeoJSON")
            return gdf_reprojected.to_json()
            
        except GeoAsystentException:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get layer as GeoJSON: {layer_name} - {e}")
            raise GISDataProcessingError(
                operation=f"converting layer {layer_name} to GeoJSON",
                original_error=e
            )
    
    @log_gis_operation("largest_parcel_search")
    def find_largest_parcel(self) -> str:
        """
        Find the single largest parcel.
        
        Returns:
            GeoJSON string with the largest parcel
        """
        self.logger.info("Finding largest parcel")
        
        try:
            criteria = ParcelCriteria(limit=1, order_by="area_sqm DESC")
            gdf = self.repository.find_parcels_by_criteria(criteria)
            
            # Reproject to WGS84
            gdf_reprojected = gdf.to_crs(epsg=4326)
            
            self.logger.info(f"Found largest parcel with {len(gdf_reprojected)} result")
            return gdf_reprojected.to_json()
            
        except Exception as e:
            self.logger.error(f"Failed to find largest parcel: {e}")
            raise
    
    @log_gis_operation("n_largest_parcels_search")
    def find_n_largest_parcels(self, n: int) -> str:
        """
        Find N largest parcels.
        
        Args:
            n: Number of parcels to find
            
        Returns:
            GeoJSON string with N largest parcels
        """
        if n <= 0:
            raise ValueError("n must be positive")
        
        self.logger.info(f"Finding {n} largest parcels")
        
        try:
            criteria = ParcelCriteria(limit=n, order_by="area_sqm DESC")
            gdf = self.repository.find_parcels_by_criteria(criteria)
            
            # Reproject to WGS84
            gdf_reprojected = gdf.to_crs(epsg=4326)
            
            self.logger.info(f"Found {len(gdf_reprojected)} largest parcels")
            return gdf_reprojected.to_json()
            
        except Exception as e:
            self.logger.error(f"Failed to find {n} largest parcels: {e}")
            raise
    
    @log_gis_operation("area_based_parcel_search")
    def find_parcels_above_area(self, min_area: float) -> str:
        """
        Find parcels with area above threshold.
        
        Args:
            min_area: Minimum area in square meters
            
        Returns:
            GeoJSON string with matching parcels
        """
        if min_area < 0:
            raise ValueError("min_area must be non-negative")
        
        self.logger.info(f"Finding parcels above {min_area} m²")
        
        try:
            criteria = ParcelCriteria(min_area=min_area, order_by="area_sqm DESC")
            gdf = self.repository.find_parcels_by_criteria(criteria)
            
            # Reproject to WGS84
            gdf_reprojected = gdf.to_crs(epsg=4326)
            
            self.logger.info(f"Found {len(gdf_reprojected)} parcels above {min_area} m²")
            return gdf_reprojected.to_json()
            
        except Exception as e:
            self.logger.error(f"Failed to find parcels above {min_area} m²: {e}")
            raise
    
    @log_gis_operation("proximity_search")
    def find_parcels_near_gpz(self, radius_meters: int) -> str:
        """
        Find parcels near GPZ points.
        
        Args:
            radius_meters: Search radius in meters
            
        Returns:
            GeoJSON string with parcels near GPZ
        """
        if radius_meters <= 0:
            raise ValueError("radius_meters must be positive")
        
        self.logger.info(f"Finding parcels within {radius_meters}m of GPZ points")
        
        try:
            gdf = self.repository.find_parcels_near_point("gpz_110kv", float(radius_meters))
            
            if gdf.empty:
                self.logger.info(f"No parcels found within {radius_meters}m of GPZ")
                # Return empty FeatureCollection
                return '{"type": "FeatureCollection", "features": []}'
            
            # Reproject to WGS84
            gdf_reprojected = gdf.to_crs(epsg=4326)
            
            self.logger.info(f"Found {len(gdf_reprojected)} parcels within {radius_meters}m of GPZ")
            return gdf_reprojected.to_json()
            
        except Exception as e:
            self.logger.error(f"Failed to find parcels near GPZ: {e}")
            raise
    
    @log_gis_operation("parcels_without_buildings_search")
    def find_parcels_without_buildings(self) -> str:
        """
        Find parcels that do not contain any buildings within their boundaries.
        
        Returns:
            GeoJSON string with parcels without buildings
        """
        self.logger.info("Finding parcels without buildings")
        
        try:
            gdf = self.repository.find_parcels_without_buildings()
            
            if gdf.empty:
                self.logger.info("No parcels without buildings found")
                # Return empty FeatureCollection
                return '{"type": "FeatureCollection", "features": []}'
            
            # Reproject to WGS84
            gdf_reprojected = gdf.to_crs(epsg=4326)
            
            # Add descriptive messages
            messages = []
            for _, row in gdf_reprojected.iterrows():
                parcel_id = row.get('ID_DZIALKI', 'Brak ID')
                area_sqm = row.get('area_sqm', 0)
                area_ha = area_sqm / 10000 if area_sqm else 0
                messages.append(f"Niezabudowana działka. ID: {parcel_id}, Powierzchnia: {area_ha:.4f} ha")
            
            gdf_reprojected['message'] = messages
            
            self.logger.info(f"Found {len(gdf_reprojected)} parcels without buildings")
            return gdf_reprojected.to_json()
            
        except Exception as e:
            self.logger.error(f"Failed to find parcels without buildings: {e}")
            raise SpatialQueryError(
                operation="finding parcels without buildings",
                original_error=e
            )
    
    def get_layer_info(self, layer_name: str) -> Dict[str, Any]:
        """
        Get information about a layer.
        
        Args:
            layer_name: Name of the layer
            
        Returns:
            Dictionary with layer information
        """
        try:
            layer_config = self.repository.get_layer_config(layer_name)
            bounds = self.repository.get_layer_bounds(layer_name)
            
            return {
                "name": layer_config.name,
                "display_name": layer_config.display_name,
                "description": layer_config.description,
                "table_name": layer_config.table_name,
                "geometry_column": layer_config.geometry_column,
                "id_column": layer_config.id_column,
                "has_low_resolution": layer_config.has_low_resolution,
                "bounds": bounds
            }
            
        except GeoAsystentException:
            raise
        except Exception as e:
            logger.error(f"Failed to get layer info: {layer_name} - {e}")
            raise
    
    def get_available_layers(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available layers.
        
        Returns:
            Dictionary with layer information
        """
        layers_info = {}
        
        for layer_name in self.repository.layers.keys():
            try:
                layers_info[layer_name] = self.get_layer_info(layer_name)
            except Exception as e:
                logger.warning(f"Failed to get info for layer {layer_name}: {e}")
                continue
        
        return layers_info
    
    @log_gis_operation("layer_statistics")
    def get_layer_statistics(self, layer_name: str) -> Dict[str, Any]:
        """
        Get statistical information about a layer.
        
        Args:
            layer_name: Name of the layer
            
        Returns:
            Dictionary with layer statistics
        """
        self.logger.info(f"Getting statistics for layer: {layer_name}")
        
        try:
            layer_config = self.repository.get_layer_config(layer_name)
            
            # Get basic layer info
            layer_info = self.get_layer_info(layer_name)
            
            # For parcels, get area statistics
            if layer_name in ["parcels", "działki"]:
                # Get some sample data to calculate statistics
                gdf = self.repository.get_layer_data(layer_name, use_low_resolution=True)
                
                if not gdf.empty and 'area_sqm' in gdf.columns:
                    area_stats = {
                        "total_parcels": len(gdf),
                        "total_area_sqm": float(gdf['area_sqm'].sum()),
                        "average_area_sqm": float(gdf['area_sqm'].mean()),
                        "min_area_sqm": float(gdf['area_sqm'].min()),
                        "max_area_sqm": float(gdf['area_sqm'].max()),
                        "median_area_sqm": float(gdf['area_sqm'].median())
                    }
                    layer_info.update(area_stats)
            
            self.logger.info(f"Successfully calculated statistics for {layer_name}")
            return layer_info
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics for layer {layer_name}: {e}")
            raise GISDataProcessingError(
                operation=f"calculating statistics for layer {layer_name}",
                original_error=e
            )
    
    @log_gis_operation("spatial_analysis")
    def analyze_parcel_distribution(self, area_thresholds: List[float] = None) -> Dict[str, Any]:
        """
        Analyze the distribution of parcels by area ranges.
        
        Args:
            area_thresholds: List of area thresholds in square meters
            
        Returns:
            Dictionary with distribution analysis
        """
        if area_thresholds is None:
            area_thresholds = [100, 500, 1000, 5000, 10000]  # Default thresholds
        
        self.logger.info(f"Analyzing parcel distribution with thresholds: {area_thresholds}")
        
        try:
            # Get parcel data
            gdf = self.repository.get_layer_data("parcels", use_low_resolution=True)
            
            if gdf.empty:
                return {"error": "No parcel data available"}
            
            # Calculate area if not present
            if 'area_sqm' not in gdf.columns:
                gdf['area_sqm'] = gdf.geometry.area
            
            # Analyze distribution
            distribution = {}
            total_parcels = len(gdf)
            
            for i, threshold in enumerate(area_thresholds):
                if i == 0:
                    # First range: 0 to threshold
                    count = len(gdf[gdf['area_sqm'] <= threshold])
                    range_name = f"0-{threshold} m²"
                else:
                    # Subsequent ranges: previous threshold to current threshold
                    prev_threshold = area_thresholds[i-1]
                    count = len(gdf[(gdf['area_sqm'] > prev_threshold) & (gdf['area_sqm'] <= threshold)])
                    range_name = f"{prev_threshold}-{threshold} m²"
                
                percentage = (count / total_parcels) * 100 if total_parcels > 0 else 0
                distribution[range_name] = {
                    "count": count,
                    "percentage": round(percentage, 2)
                }
            
            # Add range for parcels above the highest threshold
            if area_thresholds:
                highest_threshold = max(area_thresholds)
                count = len(gdf[gdf['area_sqm'] > highest_threshold])
                percentage = (count / total_parcels) * 100 if total_parcels > 0 else 0
                distribution[f">{highest_threshold} m²"] = {
                    "count": count,
                    "percentage": round(percentage, 2)
                }
            
            result = {
                "total_parcels": total_parcels,
                "distribution": distribution,
                "thresholds_used": area_thresholds
            }
            
            self.logger.info(f"Successfully analyzed distribution of {total_parcels} parcels")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze parcel distribution: {e}")
            raise GISDataProcessingError(
                operation="analyzing parcel distribution",
                original_error=e
            )
    
    @log_gis_operation("data_validation")
    def validate_layer_data(self, layer_name: str) -> Dict[str, Any]:
        """
        Validate the integrity and quality of layer data.
        
        Args:
            layer_name: Name of the layer to validate
            
        Returns:
            Dictionary with validation results
        """
        self.logger.info(f"Validating data for layer: {layer_name}")
        
        try:
            layer_config = self.repository.get_layer_config(layer_name)
            gdf = self.repository.get_layer_data(layer_name, use_low_resolution=False)
            
            validation_results = {
                "layer_name": layer_name,
                "total_features": len(gdf),
                "issues": [],
                "warnings": [],
                "is_valid": True
            }
            
            if gdf.empty:
                validation_results["issues"].append("Layer contains no data")
                validation_results["is_valid"] = False
                return validation_results
            
            # Check for null geometries
            null_geom_count = gdf.geometry.isnull().sum()
            if null_geom_count > 0:
                validation_results["issues"].append(f"{null_geom_count} features have null geometries")
                validation_results["is_valid"] = False
            
            # Check for invalid geometries
            invalid_geom_count = (~gdf.geometry.is_valid).sum()
            if invalid_geom_count > 0:
                validation_results["warnings"].append(f"{invalid_geom_count} features have invalid geometries")
            
            # Check for duplicate IDs if ID column exists
            if layer_config.id_column in gdf.columns:
                duplicate_ids = gdf[layer_config.id_column].duplicated().sum()
                if duplicate_ids > 0:
                    validation_results["issues"].append(f"{duplicate_ids} features have duplicate IDs")
                    validation_results["is_valid"] = False
            
            # Check coordinate system
            if gdf.crs is None:
                validation_results["warnings"].append("Layer has no defined coordinate reference system")
            else:
                validation_results["crs"] = str(gdf.crs)
            
            # Calculate bounds
            if not gdf.empty:
                bounds = gdf.total_bounds
                validation_results["bounds"] = {
                    "minx": float(bounds[0]),
                    "miny": float(bounds[1]),
                    "maxx": float(bounds[2]),
                    "maxy": float(bounds[3])
                }
            
            self.logger.info(f"Validation completed for {layer_name}: {'PASSED' if validation_results['is_valid'] else 'FAILED'}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Failed to validate layer {layer_name}: {e}")
            raise GISDataProcessingError(
                operation=f"validating layer {layer_name}",
                original_error=e
            )
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of available GIS operations.
        
        Returns:
            Dictionary with operation descriptions and parameters
        """
        return {
            "layer_operations": {
                "get_layer_as_geojson": {
                    "description": "Retrieve complete layer data as GeoJSON",
                    "parameters": ["layer_name", "use_low_resolution (optional)"],
                    "example": "get_layer_as_geojson('parcels')"
                },
                "get_layer_info": {
                    "description": "Get metadata about a layer",
                    "parameters": ["layer_name"],
                    "example": "get_layer_info('buildings')"
                },
                "get_layer_statistics": {
                    "description": "Get statistical information about a layer",
                    "parameters": ["layer_name"],
                    "example": "get_layer_statistics('parcels')"
                }
            },
            "parcel_operations": {
                "find_largest_parcel": {
                    "description": "Find the single largest parcel by area",
                    "parameters": [],
                    "example": "find_largest_parcel()"
                },
                "find_n_largest_parcels": {
                    "description": "Find N largest parcels by area",
                    "parameters": ["n"],
                    "example": "find_n_largest_parcels(10)"
                },
                "find_parcels_above_area": {
                    "description": "Find parcels with area above threshold",
                    "parameters": ["min_area"],
                    "example": "find_parcels_above_area(1000)"
                },
                "find_parcels_near_gpz": {
                    "description": "Find parcels within radius of GPZ points",
                    "parameters": ["radius_meters"],
                    "example": "find_parcels_near_gpz(500)"
                }
            },
            "analysis_operations": {
                "analyze_parcel_distribution": {
                    "description": "Analyze distribution of parcels by area ranges",
                    "parameters": ["area_thresholds (optional)"],
                    "example": "analyze_parcel_distribution([100, 500, 1000])"
                },
                "validate_layer_data": {
                    "description": "Validate layer data integrity and quality",
                    "parameters": ["layer_name"],
                    "example": "validate_layer_data('parcels')"
                }
            },
            "supported_layers": list(self.repository.layers.keys())
        }