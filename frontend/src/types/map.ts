/**
 * TypeScript type definitions for map and GIS operations
 */

// Coordinate and geometry types
export type Coordinate = [number, number];
export type Coordinates = Coordinate[];
export type CoordinatesArray = Coordinates[];
export type BoundingBox = [number, number, number, number]; // [minX, minY, maxX, maxY]

// Geometry types following GeoJSON specification
export interface BaseGeometry {
  type: string;
}

export interface PointGeometry extends BaseGeometry {
  type: 'Point';
  coordinates: Coordinate;
}

export interface LineStringGeometry extends BaseGeometry {
  type: 'LineString';
  coordinates: Coordinates;
}

export interface PolygonGeometry extends BaseGeometry {
  type: 'Polygon';
  coordinates: CoordinatesArray;
}

export interface MultiPointGeometry extends BaseGeometry {
  type: 'MultiPoint';
  coordinates: Coordinates;
}

export interface MultiLineStringGeometry extends BaseGeometry {
  type: 'MultiLineString';
  coordinates: CoordinatesArray;
}

export interface MultiPolygonGeometry extends BaseGeometry {
  type: 'MultiPolygon';
  coordinates: CoordinatesArray[];
}

export interface GeometryCollectionGeometry extends BaseGeometry {
  type: 'GeometryCollection';
  geometries: Geometry[];
}

export type Geometry = 
  | PointGeometry 
  | LineStringGeometry 
  | PolygonGeometry 
  | MultiPointGeometry 
  | MultiLineStringGeometry 
  | MultiPolygonGeometry 
  | GeometryCollectionGeometry;

// Feature types
export interface FeatureProperties {
  [key: string]: any;
  name?: string;
  description?: string;
  id?: string | number;
  message?: string;
}

export interface Feature {
  type: 'Feature';
  geometry: Geometry;
  properties: FeatureProperties;
  id?: string | number;
}

export interface FeatureCollection {
  type: 'FeatureCollection';
  features: Feature[];
  bbox?: BoundingBox;
}

// Layer types
export interface LayerMetadata {
  id: string | number;
  name: string;
  description?: string;
  source?: string;
  created?: Date;
  updated?: Date;
  tags?: string[];
}

export interface LayerStyle {
  color?: string;
  weight?: number;
  opacity?: number;
  fillColor?: string;
  fillOpacity?: number;
  dashArray?: string;
  radius?: number; // for point layers
}

export interface LayerInfo extends LayerMetadata {
  geometryType: 'Point' | 'LineString' | 'Polygon' | 'MultiPoint' | 'MultiLineString' | 'MultiPolygon' | 'Mixed';
  featureCount: number;
  bbox?: BoundingBox;
  srid: number;
  tableName?: string;
  visible: boolean;
  style?: LayerStyle;
  loading?: boolean;
  error?: string;
}

// Map view types
export interface MapView {
  center: Coordinate;
  zoom: number;
  bounds?: BoundingBox;
  minZoom?: number;
  maxZoom?: number;
}

export interface MapOptions extends MapView {
  attributionControl?: boolean;
  zoomControl?: boolean;
  scrollWheelZoom?: boolean;
  doubleClickZoom?: boolean;
  dragging?: boolean;
  touchZoom?: boolean;
  boxZoom?: boolean;
  keyboard?: boolean;
}

// Spatial query types
export interface SpatialQuery {
  type: 'intersects' | 'contains' | 'within' | 'touches' | 'crosses' | 'overlaps' | 'disjoint';
  geometry: Geometry;
  layers?: string[];
  properties?: Record<string, any>;
}

export interface SpatialQueryResult {
  features: Feature[];
  totalCount: number;
  executionTime?: number;
  query: SpatialQuery;
}

// Analysis types
export interface BufferAnalysis {
  geometry: Geometry;
  distance: number;
  units: 'meters' | 'kilometers' | 'feet' | 'miles';
}

export interface DistanceAnalysis {
  from: Geometry;
  to: Geometry;
  units: 'meters' | 'kilometers' | 'feet' | 'miles';
}

export interface AreaAnalysis {
  geometry: Geometry;
  units: 'square_meters' | 'square_kilometers' | 'hectares' | 'acres';
}

// Map interaction types
export interface MapClickEvent {
  latlng: Coordinate;
  layerPoint: [number, number];
  containerPoint: [number, number];
  originalEvent: MouseEvent;
}

export interface FeatureClickEvent extends MapClickEvent {
  feature: Feature;
  layer: any;
}

export interface LayerEvent {
  layer: any;
  type: string;
  target: any;
}

// Tile layer types
export interface TileLayerOptions {
  url: string;
  attribution?: string;
  maxZoom?: number;
  minZoom?: number;
  opacity?: number;
  zIndex?: number;
  subdomains?: string | string[];
}

// Marker and popup types
export interface MarkerOptions {
  position: Coordinate;
  title?: string;
  icon?: any;
  draggable?: boolean;
  opacity?: number;
  zIndexOffset?: number;
}

export interface PopupOptions {
  content: string;
  maxWidth?: number;
  minWidth?: number;
  maxHeight?: number;
  autoPan?: boolean;
  closeButton?: boolean;
  autoClose?: boolean;
  closeOnEscapeKey?: boolean;
}

// Export utility types
export type GeometryType = Geometry['type'];
export type FeatureType = Feature['type'];
export type FeatureCollectionType = FeatureCollection['type'];