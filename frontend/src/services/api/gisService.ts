/**
 * GIS API service for layer operations and spatial queries
 */

import { ApiClient } from './client';
import { API_ENDPOINTS } from './config';
import type {
  GeoJsonFeatureCollection,
  LayerInfo,
  LayerListResponse,
  LayerStatistics,
  LayerValidationResult,
  ParcelDistributionRequest,
  ParcelDistributionResponse,
  RequestOptions,
} from './types';

export class GISService {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /**
   * Get all available layers with metadata
   */
  async getLayers(options?: RequestOptions): Promise<LayerInfo[]> {
    const response = await this.apiClient.get<LayerListResponse>(
      API_ENDPOINTS.LAYERS.BASE,
      {},
      options
    );
    return response.data.layers;
  }

  /**
   * Get a specific layer as GeoJSON
   */
  async getLayer(
    layerName: string,
    useLowResolution: boolean = true,
    options?: RequestOptions
  ): Promise<GeoJsonFeatureCollection> {
    const params = new URLSearchParams();
    if (useLowResolution !== undefined) {
      params.append('use_low_resolution', useLowResolution.toString());
    }
  
    const url = `${API_ENDPOINTS.LAYERS.BY_NAME(layerName)}${params.toString() ? `?${params.toString()}` : ''}`;
  
    const response = await this.apiClient.get<GeoJsonFeatureCollection>(url, {}, options);
  
    return response.data as GeoJsonFeatureCollection;
  }

  /**
   * Get layer statistics
   */
  async getLayerStatistics(
    layerName: string,
    options?: RequestOptions
  ): Promise<LayerStatistics> {
    const response = await this.apiClient.get<LayerStatistics>(
      API_ENDPOINTS.LAYERS.STATISTICS(layerName),
      {},
      options
    );
    return response.data;
  }

  /**
   * Validate layer data integrity
   */
  async validateLayer(
    layerName: string,
    options?: RequestOptions
  ): Promise<LayerValidationResult> {
    const response = await this.apiClient.get<LayerValidationResult>(
      API_ENDPOINTS.LAYERS.VALIDATE(layerName),
      {},
      options
    );
    return response.data;
  }

  /**
   * Analyze parcel distribution by area ranges
   */
  async analyzeParcelDistribution(
    request: ParcelDistributionRequest = {},
    options?: RequestOptions
  ): Promise<ParcelDistributionResponse> {
    const params = new URLSearchParams();
    if (request.thresholds && request.thresholds.length > 0) {
      request.thresholds.forEach(threshold => {
        params.append('thresholds', threshold.toString());
      });
    }

    const url = `${API_ENDPOINTS.ANALYSIS.PARCEL_DISTRIBUTION}${params.toString() ? `?${params.toString()}` : ''}`;
    
    const response = await this.apiClient.get<ParcelDistributionResponse>(url, {}, options);
    return response.data;
  }

  /**
   * Batch load multiple layers
   */
  async getMultipleLayers(
    layerNames: string[],
    useLowResolution: boolean = true,
    options?: RequestOptions
  ): Promise<Array<{ name: string; data: GeoJsonFeatureCollection; error?: string }>> {
    const results = await Promise.allSettled(
      layerNames.map(async (name) => {
        try {
          const data = await this.getLayer(name, useLowResolution, options);
          return { name, data };
        } catch (error) {
          return { 
            name, 
            data: { type: 'FeatureCollection' as const, features: [] },
            error: error instanceof Error ? error.message : 'Unknown error'
          };
        }
      })
    );

    return results.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return {
          name: layerNames[index],
          data: { type: 'FeatureCollection' as const, features: [] },
          error: result.reason?.message || 'Failed to load layer'
        };
      }
    });
  }

  /**
   * Check if a layer exists
   */
  async layerExists(layerName: string, options?: RequestOptions): Promise<boolean> {
    try {
      await this.getLayerStatistics(layerName, options);
      return true;
    } catch (error: any) {
      if (error.status === 404) {
        return false;
      }
      throw error;
    }
  }
}