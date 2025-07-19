/**
 * Main types module - exports all type definitions
 */

// Common utility types
export * from './common';

// Map and GIS types
export * from './map';

// Component types
export * from './components';

// Re-export specific API types to avoid conflicts
export type {
  ApiConfig,
  HttpMethod,
  RequestConfig,
  ChatRequest,
  ChatResponse,
  GeoJsonFeature,
  GeoJsonFeatureCollection,
  LayerListResponse,
  LayerStatistics,
  LayerValidationResult,
  ParcelDistributionRequest,
  ParcelDistributionResponse,
  RequestOptions
} from '../services/api/types';

// Re-export hook types for convenience
export type { 
  Message, 
  UseChatReturn 
} from '../hooks/useChat';

export type { 
  LayerState, 
  LayerConfig, 
  UseMapLayersReturn 
} from '../hooks/useMapLayers';

export type { 
  UseErrorHandlerReturn 
} from '../hooks/useErrorHandler';