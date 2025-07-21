"""Domain models for Geo-Asystent AI."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, Union, Literal
from enum import Enum


class LayerType(str, Enum):
    """Types of GIS layers."""
    PARCELS = "parcels"
    BUILDINGS = "buildings"
    GPZ = "gpz"


@dataclass
class LayerConfig:
    """Configuration for a GIS layer."""
    name: str
    table_name: str
    geometry_column: str
    id_column: str
    display_name: str
    description: Optional[str] = None
    layer_type: Optional[LayerType] = None


@dataclass
class ParcelCriteria:
    """Criteria for parcel queries."""
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    limit: Optional[int] = None
    order_by: str = "area_sqm DESC"
    
    def __post_init__(self):
        """Validate criteria after initialization."""
        if self.min_area is not None and self.min_area < 0:
            raise ValueError("min_area must be non-negative")
        if self.max_area is not None and self.max_area < 0:
            raise ValueError("max_area must be non-negative")
        if self.min_area is not None and self.max_area is not None and self.min_area > self.max_area:
            raise ValueError("min_area cannot be greater than max_area")
        if self.limit is not None and self.limit <= 0:
            raise ValueError("limit must be positive")


@dataclass
class QueryResult:
    """Result of a query operation."""
    type: Literal['geojson', 'text']
    data: Union[str, Dict[str, Any]]
    intent: str
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SpatialQuery:
    """Configuration for spatial queries."""
    query_type: str
    parameters: Dict[str, Any]
    target_layer: str
    reference_layer: Optional[str] = None
    
    def __post_init__(self):
        """Validate spatial query configuration."""
        if not self.query_type:
            raise ValueError("query_type is required")
        if not self.target_layer:
            raise ValueError("target_layer is required")


@dataclass
class GISOperationResult:
    """Result of a GIS operation."""
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    operation_type: Optional[str] = None
    duration: Optional[float] = None
    feature_count: Optional[int] = None
    
    @classmethod
    def success_result(cls, data: Any, operation_type: str, duration: float = None, feature_count: int = None):
        """Create a successful result."""
        return cls(
            success=True,
            data=data,
            operation_type=operation_type,
            duration=duration,
            feature_count=feature_count
        )
    
    @classmethod
    def error_result(cls, error_message: str, operation_type: str, duration: float = None):
        """Create an error result."""
        return cls(
            success=False,
            error_message=error_message,
            operation_type=operation_type,
            duration=duration
        )