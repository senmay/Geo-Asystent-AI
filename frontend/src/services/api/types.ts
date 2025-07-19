/**
 * TypeScript type definitions for API requests and responses
 */

import type { Feature, FeatureCollection } from '../../types/map';

// Configuration types
export interface ApiConfig {
  baseURL: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
  headers?: Record<string, string>;
}

// Base types
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  statusText: string;
  headers?: Record<string, string>;
}

export interface ApiError {
  message: string;
  status?: number;
  code?: string;
  details?: any;
  timestamp?: Date;
  requestId?: string;
}

// HTTP method types
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH' | 'HEAD' | 'OPTIONS';

// Request configuration
export interface RequestConfig {
  method?: HttpMethod;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  data?: any;
  timeout?: number;
  retries?: number;
  signal?: AbortSignal;
}

// Chat API types
export interface ChatRequest {
  query: string;
  context?: Record<string, any>;
}

export interface ChatResponse {
  type: 'text' | 'geojson';
  data: string;
  intent: string;
  metadata?: Record<string, any>;
}

// GeoJSON types (re-exported from map types for convenience)
export type GeoJsonFeature = Feature;
export type GeoJsonFeatureCollection = FeatureCollection;

// Layer types
export interface LayerInfo {
  name: string;
  table_name: string;
  geometry_type: string;
  srid: number;
  feature_count: number;
  bbox?: [number, number, number, number];
}

export interface LayerListResponse {
  layers: LayerInfo[];
}

export interface LayerStatistics {
  feature_count: number;
  geometry_type: string;
  srid: number;
  bbox: [number, number, number, number];
  area_statistics?: {
    min_area: number;
    max_area: number;
    avg_area: number;
    total_area: number;
  };
}

export interface LayerValidationResult {
  is_valid: boolean;
  issues: Array<{
    type: string;
    message: string;
    feature_id?: number;
  }>;
  summary: {
    total_features: number;
    valid_features: number;
    invalid_features: number;
  };
}

// Analysis types
export interface ParcelDistributionRequest {
  thresholds?: number[];
}

export interface ParcelDistributionResponse {
  distribution: Array<{
    range: string;
    count: number;
    percentage: number;
    total_area: number;
  }>;
  summary: {
    total_parcels: number;
    total_area: number;
    average_area: number;
  };
}

// Request options
export interface RequestOptions {
  timeout?: number;
  retries?: number;
  signal?: AbortSignal;
}