"""
Simplified layer configuration service.
Eliminates shotgun surgery when adding new layers.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from sqlalchemy.engine import Engine
from sqlalchemy import text

logger = logging.getLogger(__name__)


@dataclass
class LayerStyle:
    """Layer styling configuration."""
    point_color: str = '#ff7800'
    point_radius: int = 6
    point_opacity: float = 0.8
    point_fill_opacity: float = 0.8
    
    line_color: str = '#3388ff'
    line_weight: int = 3
    line_opacity: float = 0.7
    line_dash_array: Optional[str] = None
    
    polygon_color: str = '#3388ff'
    polygon_weight: int = 2
    polygon_opacity: float = 0.7
    polygon_fill_color: Optional[str] = None
    polygon_fill_opacity: float = 0.2


@dataclass
class LayerConfig:
    """Complete layer configuration."""
    layer_name: str
    display_name: str
    table_name: str
    geometry_column: str = 'geometry'
    id_column: str = 'id'
    description: Optional[str] = None
    
    style: LayerStyle = None
    
    default_visible: bool = False
    min_zoom: int = 0
    max_zoom: int = 20
    cluster_points: bool = True
    active: bool = True
    
    def __post_init__(self):
        if self.style is None:
            self.style = LayerStyle()


class LayerConfigService:
    """Service for managing layer configurations from database."""
    
    def __init__(self, db_engine: Engine):
        self.db_engine = db_engine
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._cache = {}
        self._cache_loaded = False
    
    def get_layer_config(self, layer_name: str) -> Optional[LayerConfig]:
        """Get configuration for a specific layer."""
        self._ensure_cache_loaded()
        return self._cache.get(layer_name)
    
    def get_all_layers(self) -> Dict[str, LayerConfig]:
        """Get all active layer configurations."""
        self._ensure_cache_loaded()
        return self._cache.copy()
    
    def get_visible_layers(self) -> Dict[str, LayerConfig]:
        """Get layers that should be visible by default."""
        self._ensure_cache_loaded()
        return {
            name: config for name, config in self._cache.items()
            if config.default_visible
        }
    
    def refresh_cache(self):
        """Refresh the configuration cache from database."""
        self._cache_loaded = False
        self._ensure_cache_loaded()
    
    def _ensure_cache_loaded(self):
        """Load configurations from database if not already loaded."""
        if self._cache_loaded:
            return
        
        try:
            self._load_from_database()
            self._cache_loaded = True
            self.logger.info(f"Loaded {len(self._cache)} layer configurations")
        except Exception as e:
            self.logger.error(f"Failed to load layer configurations: {e}")
            self._load_fallback_config()
    
    def _load_from_database(self):
        """Load layer configurations from database."""
        sql = """
        SELECT 
            layer_name, display_name, table_name, geometry_column, id_column,
            description, point_color, point_radius, point_opacity, point_fill_opacity,
            line_color, line_weight, line_opacity, line_dash_array,
            polygon_color, polygon_weight, polygon_opacity, polygon_fill_color, polygon_fill_opacity,
            default_visible, min_zoom, max_zoom, cluster_points, active
        FROM layer_config 
        WHERE active = true
        ORDER BY layer_name
        """
        
        with self.db_engine.connect() as conn:
            result = conn.execute(text(sql))
            
            for row in result:
                style = LayerStyle(
                    point_color=row.point_color,
                    point_radius=row.point_radius,
                    point_opacity=float(row.point_opacity),
                    point_fill_opacity=float(row.point_fill_opacity),
                    
                    line_color=row.line_color,
                    line_weight=row.line_weight,
                    line_opacity=float(row.line_opacity),
                    line_dash_array=row.line_dash_array,
                    
                    polygon_color=row.polygon_color,
                    polygon_weight=row.polygon_weight,
                    polygon_opacity=float(row.polygon_opacity),
                    polygon_fill_color=row.polygon_fill_color,
                    polygon_fill_opacity=float(row.polygon_fill_opacity)
                )
                
                config = LayerConfig(
                    layer_name=row.layer_name,
                    display_name=row.display_name,
                    table_name=row.table_name,
                    geometry_column=row.geometry_column,
                    id_column=row.id_column,
                    description=row.description,
                    style=style,
                    default_visible=row.default_visible,
                    min_zoom=row.min_zoom,
                    max_zoom=row.max_zoom,
                    cluster_points=row.cluster_points,
                    active=row.active
                )
                
                self._cache[row.layer_name] = config
    
    # def _load_fallback_config(self):
    #     """Load fallback configuration if database is not available."""
    #     self.logger.warning("Using fallback layer configuration")
        
    #     fallback_configs = [
    #         LayerConfig(
    #             layer_name='parcels',
    #             display_name='Działki przykładowe',
    #             table_name='parcels',
    #             geometry_column='geometry',
    #             id_column='ID_DZIALKI',
    #             description='Działki ewidencyjne',
    #             default_visible=True,
    #             cluster_points=False
    #         ),
    #         LayerConfig(
    #             layer_name='buildings',
    #             display_name='Budynki przykładowe',
    #             table_name='buildings',
    #             geometry_column='geometry',
    #             id_column='ID_BUDYNKU',
    #             description='Kontury budynków',
    #             default_visible=True,
    #             cluster_points=False
    #         ),
    #         LayerConfig(
    #             layer_name='gpz_POLSKA',
    #             display_name='GPZ 110kV',
    #             table_name='gpz_110kv',
    #             geometry_column='geom',
    #             id_column='id',
    #             description='Stacje elektroenergetyczne',
    #             default_visible=True,
    #             cluster_points=True
    #         )
    #     ]
        
    #     for config in fallback_configs:
    #         self._cache[config.layer_name] = config
    
    def add_layer_config(self, config: LayerConfig) -> bool:
        """Add or update layer configuration in database."""
        try:
            sql = """
            INSERT INTO layer_config (
                layer_name, display_name, table_name, geometry_column, id_column,
                description, point_color, point_radius, point_opacity, point_fill_opacity,
                line_color, line_weight, line_opacity, line_dash_array,
                polygon_color, polygon_weight, polygon_opacity, polygon_fill_color, polygon_fill_opacity,
                default_visible, min_zoom, max_zoom, cluster_points, active
            ) VALUES (
                :layer_name, :display_name, :table_name, :geometry_column, :id_column,
                :description, :point_color, :point_radius, :point_opacity, :point_fill_opacity,
                :line_color, :line_weight, :line_opacity, :line_dash_array,
                :polygon_color, :polygon_weight, :polygon_opacity, :polygon_fill_color, :polygon_fill_opacity,
                :default_visible, :min_zoom, :max_zoom, :cluster_points, :active
            )
            ON CONFLICT (layer_name) DO UPDATE SET
                display_name = EXCLUDED.display_name,
                description = EXCLUDED.description,
                point_color = EXCLUDED.point_color,
                polygon_color = EXCLUDED.polygon_color,
                default_visible = EXCLUDED.default_visible,
                updated_at = CURRENT_TIMESTAMP
            """
            
            with self.db_engine.connect() as conn:
                conn.execute(text(sql), {
                    'layer_name': config.layer_name,
                    'display_name': config.display_name,
                    'table_name': config.table_name,
                    'geometry_column': config.geometry_column,
                    'id_column': config.id_column,
                    'description': config.description,
                    'point_color': config.style.point_color,
                    'point_radius': config.style.point_radius,
                    'point_opacity': config.style.point_opacity,
                    'point_fill_opacity': config.style.point_fill_opacity,
                    'line_color': config.style.line_color,
                    'line_weight': config.style.line_weight,
                    'line_opacity': config.style.line_opacity,
                    'line_dash_array': config.style.line_dash_array,
                    'polygon_color': config.style.polygon_color,
                    'polygon_weight': config.style.polygon_weight,
                    'polygon_opacity': config.style.polygon_opacity,
                    'polygon_fill_color': config.style.polygon_fill_color,
                    'polygon_fill_opacity': config.style.polygon_fill_opacity,
                    'default_visible': config.default_visible,
                    'min_zoom': config.min_zoom,
                    'max_zoom': config.max_zoom,
                    'cluster_points': config.cluster_points,
                    'active': config.active
                })
                conn.commit()
            
            # Refresh cache
            self.refresh_cache()
            self.logger.info(f"Added/updated layer configuration: {config.layer_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add layer configuration: {e}")
            return False