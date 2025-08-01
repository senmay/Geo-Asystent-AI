"""GIS service layer for business logic."""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
import geopandas as gpd
from sqlalchemy.engine import Engine

from repositories import GISRepository
from models.domain import ParcelCriteria, QueryResult, GISOperationResult
from exceptions import (
    GeoAsystentException, 
    GISDataProcessingError, 
    SpatialQueryError,
    DatabaseConnectionError,
    LayerNotFoundError,
    InvalidLayerNameError,
    ValidationError
)
from utils.db_logger import log_gis_operation
from utils.result_helpers import limit_results_for_display, add_simple_id_messages, add_parcel_messages, convert_to_geojson
from utils.validation_helpers import validate_positive_integer, validate_non_negative_number, validate_area_thresholds

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
    
    def _process_parcel_results(self, gdf: gpd.GeoDataFrame, operation_type: str = "standard") -> gpd.GeoDataFrame:
        """
        Process parcel results with messages for chat display.
        
        Args:
            gdf: Raw parcel GeoDataFrame
            operation_type: Type of operation for message formatting
            
        Returns:
            Processed GeoDataFrame with all geometries but limited chat messages
        """
        if gdf.empty:
            return gdf
        
        # Add appropriate messages based on operation type
        if operation_type == "unbuilt":
            gdf_with_messages = add_parcel_messages(gdf, message_type="unbuilt")
        elif operation_type == "largest":
            gdf_with_messages = add_parcel_messages(gdf, message_type="largest")
        elif operation_type == "numbered":
            gdf_with_messages = add_parcel_messages(gdf, message_type="numbered")
        else:
            gdf_with_messages = add_parcel_messages(gdf, message_type="standard")
        
        # For chat display: limit messages to 5 but keep all geometries for map
        if len(gdf_with_messages) > 5:
            # Create messages for first 5 items only
            limited_messages = gdf_with_messages['message'].head(5).tolist()
            
            # Add summary message to the last displayed item
            total_count = len(gdf_with_messages)
            remaining = total_count - 5
            summary = f"Na czacie wyświetlono informacje o 5 z {total_count} działek. Na mapie widoczne są wszystkie {total_count} działek. Szczegółowe informacje o pozostałych {remaining} działkach dostępne w PDF."
            
            if limited_messages:
                limited_messages[-1] = f"{limited_messages[-1]}\n\n{summary}"
            
            # Create new message column: first 5 with messages, rest empty for map display
            all_messages = [''] * len(gdf_with_messages)
            for i, msg in enumerate(limited_messages):
                all_messages[i] = msg
            
            gdf_with_messages['message'] = all_messages
        
        return gdf_with_messages
    
    def _get_parcels_by_criteria(self, criteria: ParcelCriteria) -> gpd.GeoDataFrame:
        """
        Get parcels by criteria and handle common error cases.
        
        Args:
            criteria: Parcel search criteria
            
        Returns:
            GeoDataFrame with parcel results
        """
        try:
            return self.repository.find_parcels_by_criteria(criteria)
        except (LayerNotFoundError, InvalidLayerNameError, SpatialQueryError, DatabaseConnectionError):
            # Re-raise specific GIS exceptions
            raise
        except Exception as e:
            self.logger.error(f"Failed to retrieve parcels with criteria {criteria.__dict__}: {e}")
            raise GISDataProcessingError(
                operation=f"retrieving parcels with criteria {criteria.__dict__}",
                original_error=e
            )
    
    def _get_parcels_near_points(self, layer_name: str, radius_meters: float) -> gpd.GeoDataFrame:
        """
        Get parcels near points from specified layer.
        
        Args:
            layer_name: Name of the point layer
            radius_meters: Search radius in meters
            
        Returns:
            GeoDataFrame with parcel results
        """
        try:
            return self.repository.find_parcels_near_point(layer_name, radius_meters)
        except (LayerNotFoundError, InvalidLayerNameError, SpatialQueryError, DatabaseConnectionError):
            # Re-raise specific GIS exceptions
            raise
        except Exception as e:
            self.logger.error(f"Failed to find parcels near {layer_name} within {radius_meters}m: {e}")
            raise GISDataProcessingError(
                operation=f"finding parcels near {layer_name} within {radius_meters}m",
                original_error=e
            )
    
    def _get_parcels_without_buildings(self) -> gpd.GeoDataFrame:
        """
        Get parcels that do not contain buildings.
        
        Returns:
            GeoDataFrame with parcel results
        """
        try:
            return self.repository.find_parcels_without_buildings()
        except (LayerNotFoundError, InvalidLayerNameError, SpatialQueryError, DatabaseConnectionError):
            # Re-raise specific GIS exceptions
            raise
        except Exception as e:
            self.logger.error(f"Failed to find parcels without buildings: {e}")
            raise SpatialQueryError(
                query_type="finding parcels without buildings",
                parameters={},
                original_error=e
            )
    
    def _get_parcel_data_with_area(self) -> gpd.GeoDataFrame:
        """
        Get parcel data and ensure area column exists.
        
        Returns:
            GeoDataFrame with area_sqm column
        """
        gdf = self.repository.get_layer_data("dzialki")
        
        # Calculate area if not present
        if not gdf.empty and 'area_sqm' not in gdf.columns:
            gdf['area_sqm'] = gdf.geometry.area
        
        return gdf
    
    def _calculate_area_distribution(self, gdf: gpd.GeoDataFrame, thresholds: List[float]) -> Dict[str, Dict[str, Any]]:
        """
        Calculate area distribution for given thresholds.
        
        Args:
            gdf: GeoDataFrame with area_sqm column
            thresholds: List of area thresholds
            
        Returns:
            Dictionary with distribution data
        """
        distribution = {}
        total_parcels = len(gdf)
        
        for i, threshold in enumerate(thresholds):
            if i == 0:
                # First range: 0 to threshold
                count = len(gdf[gdf['area_sqm'] <= threshold])
                range_name = f"0-{threshold} m²"
            else:
                # Subsequent ranges: previous threshold to current threshold
                prev_threshold = thresholds[i-1]
                count = len(gdf[(gdf['area_sqm'] > prev_threshold) & (gdf['area_sqm'] <= threshold)])
                range_name = f"{prev_threshold}-{threshold} m²"
            
            percentage = (count / total_parcels) * 100 if total_parcels > 0 else 0
            distribution[range_name] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
        
        # Add range for parcels above the highest threshold
        if thresholds:
            highest_threshold = max(thresholds)
            count = len(gdf[gdf['area_sqm'] > highest_threshold])
            percentage = (count / total_parcels) * 100 if total_parcels > 0 else 0
            distribution[f">{highest_threshold} m²"] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
        
        return distribution
    
    def _calculate_parcel_area_statistics(self, layer_name: str) -> Dict[str, Any]:
        """
        Calculate area statistics for parcel layers.
        
        Args:
            layer_name: Name of the parcel layer
            
        Returns:
            Dictionary with area statistics
        """
        gdf = self.repository.get_layer_data(layer_name)
        
        if gdf.empty or 'area_sqm' not in gdf.columns:
            return {}
        
        return {
            "total_parcels": len(gdf),
            "total_area_sqm": float(gdf['area_sqm'].sum()),
            "average_area_sqm": float(gdf['area_sqm'].mean()),
            "min_area_sqm": float(gdf['area_sqm'].min()),
            "max_area_sqm": float(gdf['area_sqm'].max()),
            "median_area_sqm": float(gdf['area_sqm'].median())
        }
    
    @log_gis_operation("layer_retrieval")
    def get_layer_as_geojson(self, layer_name: str) -> str:
        """
        Get layer data as GeoJSON string.
        
        Args:
            layer_name: Name of the layer to retrieve
            
        Returns:
            GeoJSON string
            
        Raises:
            GeoAsystentException: If operation fails
        """
        self.logger.info(f"Retrieving layer as GeoJSON: {layer_name}")
        
        try:
            # Business logic
            gdf = self.repository.get_layer_data(layer_name)
            
            # Add ID messages if ID column exists
            layer_config = self.repository.get_layer_config(layer_name)
            if layer_config.id_column in gdf.columns:
                gdf = add_simple_id_messages(gdf, layer_config.id_column)
            
            self.logger.info(f"Successfully converted {len(gdf)} features to GeoJSON")
            return convert_to_geojson(gdf)
            
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
        
        # Business logic
        criteria = ParcelCriteria(limit=1, order_by="area_sqm DESC")
        gdf = self._get_parcels_by_criteria(criteria)
        
        # Result processing
        processed_gdf = self._process_parcel_results(gdf, operation_type="largest")
        
        self.logger.info(f"Found largest parcel with {len(gdf)} result")
        return convert_to_geojson(processed_gdf)
    
    @log_gis_operation("n_largest_parcels_search")
    def find_n_largest_parcels(self, n: int) -> str:
        """
        Find N largest parcels.
        
        Args:
            n: Number of parcels to find
            
        Returns:
            GeoJSON string with N largest parcels
        """
        # Input validation
        validate_positive_integer(n, "n")
        
        self.logger.info(f"Finding {n} largest parcels")
        
        # Business logic
        criteria = ParcelCriteria(limit=n, order_by="area_sqm DESC")
        gdf = self._get_parcels_by_criteria(criteria)
        
        # Result processing
        processed_gdf = self._process_parcel_results(gdf, operation_type="numbered")
        
        self.logger.info(f"Found {len(gdf)} largest parcels")
        return convert_to_geojson(processed_gdf)
    
    @log_gis_operation("area_based_parcel_search")
    def find_parcels_above_area(self, min_area: float) -> str:
        """
        Find parcels with area above threshold.
        
        Args:
            min_area: Minimum area in square meters
            
        Returns:
            GeoJSON string with matching parcels
        """
        # Input validation
        validate_non_negative_number(min_area, "min_area")
        
        self.logger.info(f"Finding parcels above {min_area} m²")
        
        # Business logic
        criteria = ParcelCriteria(min_area=min_area, order_by="area_sqm DESC")
        gdf = self._get_parcels_by_criteria(criteria)
        
        # Result processing
        processed_gdf = self._process_parcel_results(gdf)
        
        self.logger.info(f"Found {len(gdf)} parcels above {min_area} m²")
        return convert_to_geojson(processed_gdf)
    
    @log_gis_operation("proximity_search")
    def find_parcels_near_gpz(self, radius_meters: int) -> str:
        """
        Find parcels near GPZ points.
        
        Args:
            radius_meters: Search radius in meters
            
        Returns:
            GeoJSON string with parcels near GPZ
        """
        # Input validation
        validate_positive_integer(radius_meters, "radius_meters")
        
        self.logger.info(f"Finding parcels within {radius_meters}m of GPZ points")
        
        # Business logic
        gdf = self._get_parcels_near_points("gpz_110kv", float(radius_meters))
        
        if gdf.empty:
            self.logger.info(f"No parcels found within {radius_meters}m of GPZ")
            return convert_to_geojson(gdf)
        
        # Result processing
        processed_gdf = self._process_parcel_results(gdf)
        
        self.logger.info(f"Found {len(gdf)} parcels within {radius_meters}m of GPZ")
        return convert_to_geojson(processed_gdf)
    
    @log_gis_operation("parcels_without_buildings_search")
    def find_parcels_without_buildings(self) -> str:
        """
        Find parcels that do not contain any buildings within their boundaries.
        
        Returns:
            GeoJSON string with parcels without buildings
        """
        self.logger.info("Finding parcels without buildings")
        
        # Business logic
        gdf = self._get_parcels_without_buildings()
        
        if gdf.empty:
            self.logger.info("No parcels without buildings found")
            return convert_to_geojson(gdf)
        
        # Result processing
        processed_gdf = self._process_parcel_results(gdf, operation_type="unbuilt")
        
        self.logger.info(f"Found {len(gdf)} parcels without buildings")
        return convert_to_geojson(processed_gdf)
    
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

                "bounds": bounds
            }
            
        except (LayerNotFoundError, InvalidLayerNameError, DatabaseConnectionError):
            # Re-raise specific GIS exceptions
            raise
        except Exception as e:
            logger.error(f"Failed to get layer info for {layer_name}: {e}")
            raise GISDataProcessingError(
                operation=f"getting layer info for {layer_name}",
                original_error=e
            )
    
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
            except (LayerNotFoundError, InvalidLayerNameError, DatabaseConnectionError, GISDataProcessingError) as e:
                logger.warning(f"Failed to get info for layer {layer_name}: {e.message}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error getting info for layer {layer_name}: {e}")
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
            # Get basic layer info
            layer_info = self.get_layer_info(layer_name)
            
            # Add specific statistics for parcels
            if layer_name in ["dzialki", "działki"]:
                area_stats = self._calculate_parcel_area_statistics(layer_name)
                layer_info.update(area_stats)
            
            self.logger.info(f"Successfully calculated statistics for {layer_name}")
            return layer_info
            
        except (LayerNotFoundError, InvalidLayerNameError, DatabaseConnectionError, GISDataProcessingError):
            # Re-raise specific GIS exceptions
            raise
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
        # Input validation and defaults
        if area_thresholds is None:
            area_thresholds = [100, 500, 1000, 5000, 10000]  # Default thresholds
        else:
            validate_area_thresholds(area_thresholds)
        
        self.logger.info(f"Analyzing parcel distribution with thresholds: {area_thresholds}")
        
        try:
            # Business logic
            gdf = self._get_parcel_data_with_area()
            
            if gdf.empty:
                return {"error": "No parcel data available"}
            
            # Analysis processing
            distribution = self._calculate_area_distribution(gdf, area_thresholds)
            
            result = {
                "total_parcels": len(gdf),
                "distribution": distribution,
                "thresholds_used": area_thresholds
            }
            
            self.logger.info(f"Successfully analyzed distribution of {len(gdf)} parcels")
            return result
            
        except (LayerNotFoundError, InvalidLayerNameError, DatabaseConnectionError, GISDataProcessingError, ValidationError):
            # Re-raise specific exceptions
            raise
        except Exception as e:
            self.logger.error(f"Failed to analyze parcel distribution with thresholds {area_thresholds}: {e}")
            raise GISDataProcessingError(
                operation=f"analyzing parcel distribution with thresholds {area_thresholds}",
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
            gdf = self.repository.get_layer_data(layer_name)
            
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
            
        except (LayerNotFoundError, InvalidLayerNameError, DatabaseConnectionError, GISDataProcessingError):
            # Re-raise specific GIS exceptions
            raise
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