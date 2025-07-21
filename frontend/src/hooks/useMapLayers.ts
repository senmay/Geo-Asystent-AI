/**
 * Custom hook to manage layer state and operations
 */

import { useState, useEffect, useCallback } from 'react';
import { getGISService } from '../services';
import { useErrorHandler } from './useErrorHandler';
import type { GeoJsonFeatureCollection } from '../services/api/types';

export interface LayerState {
  id: number;
  name: string;
  data: GeoJsonFeatureCollection;
  visible: boolean;
  color?: string;
  loading?: boolean;
  error?: string;
  type?: 'geojson' | 'wms';
  wmsConfig?: WMSConfig;
  style?: {
    pointColor?: string;
    pointRadius?: number;
    pointOpacity?: number;
    pointFillOpacity?: number;
    lineColor?: string;
    lineWeight?: number;
    lineOpacity?: number;
    polygonColor?: string;
    polygonWeight?: number;
    polygonOpacity?: number;
    polygonFillColor?: string;
    polygonFillOpacity?: number;
  };
}

export interface LayerConfig {
  name: string;
  apiName: string;
  color: string;
  type?: 'geojson' | 'wms';
  wmsConfig?: WMSConfig;
}

export interface WMSConfig {
  url: string;
  layers: string;
  format?: string;
  transparent?: boolean;
  opacity?: number;
  maxZoom?: number;
  minZoom?: number;
}

export interface UseMapLayersReturn {
  layers: LayerState[];
  queryResult: GeoJsonFeatureCollection | null;
  isLoading: boolean;
  error: string | null;
  toggleLayerVisibility: (layerId: number) => void;
  refreshLayer: (layerId: number) => Promise<void>;
  addLayer: (config: LayerConfig) => Promise<void>;
  removeLayer: (layerId: number) => void;
  setQueryResult: (result: GeoJsonFeatureCollection | null) => void;
  clearError: () => void;
}

// WMS layers configuration - these are external services not in our database
const WMS_LAYERS: LayerConfig[] = [
  {
    name: 'Działki ewidencyjne z powiatów',
    apiName: 'wms_dzialki',
    color: '#45b7d1',
    type: 'wms',
    wmsConfig: {
      url: 'https://integracja.gugik.gov.pl/cgi-bin/KrajowaIntegracjaEwidencjiGruntow',
      layers: 'dzialki',
      format: 'image/png',
      transparent: true,
      opacity: 0.9,
      maxZoom: 20
    }
  },
  {
    name: 'Numery działek',
    apiName: 'wms_numery',
    color: '#45b7d1',
    type: 'wms',
    wmsConfig: {
      url: 'https://integracja.gugik.gov.pl/cgi-bin/KrajowaIntegracjaEwidencjiGruntow',
      layers: 'numery_dzialek',
      format: 'image/png',
      transparent: true,
      opacity: 1,
      maxZoom: 20
    }
  },
  {
    name: 'Kontury klasyfikacyjne',
    apiName: 'wms_kontury',
    color: '#45b7d1',
    type: 'wms',
    wmsConfig: {
      url: 'https://integracja.gugik.gov.pl/cgi-bin/KrajowaIntegracjaEwidencjiGruntow',
      layers: 'kontury',
      format: 'image/png',
      transparent: true,
      opacity: 0.8,
      maxZoom: 20
    }
  },
  {
    name: 'Użytki gruntowe',
    apiName: 'wms_uzytki',
    color: '#45b7d1',
    type: 'wms',
    wmsConfig: {
      url: 'https://integracja.gugik.gov.pl/cgi-bin/KrajowaIntegracjaEwidencjiGruntow',
      layers: 'uzytki',
      format: 'image/png',
      transparent: true,
      opacity: 0.9,
      maxZoom: 20
    }
  }
];

export const useMapLayers = (): UseMapLayersReturn => {
  const [layers, setLayers] = useState<LayerState[]>([]);
  const [queryResult, setQueryResult] = useState<GeoJsonFeatureCollection | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [layerConfigs, setLayerConfigs] = useState<LayerConfig[]>([]);
  const { error, handleError, clearError } = useErrorHandler();

  // Load layer configurations and initial layers on mount
  useEffect(() => {
    const loadLayerConfigurations = async () => {
      setIsLoading(true);
      clearError();

      try {
        // First fetch layer configurations from API
        const response = await fetch('/api/v1/layers/config');
        if (!response.ok) {
          throw new Error(`Failed to fetch layer config: ${response.status}`);
        }
        
        const data = await response.json();
        const apiLayerConfigs = data.layers;
        
        // Convert API layer config to our internal format
        const geojsonLayers: LayerConfig[] = apiLayerConfigs.map((layer: any) => ({
          name: layer.displayName,
          apiName: layer.layerName,
          color: layer.style.polygonColor || layer.style.lineColor || layer.style.pointColor,
          type: 'geojson' as const
        }));
        
        // Combine with WMS layers
        const allLayers = [...geojsonLayers, ...WMS_LAYERS];
        setLayerConfigs(allLayers);
        
        // Then load the actual layer data
        const gisService = getGISService();
        const layerPromises = allLayers.map(async (layerConfig, index) => {
          // Find corresponding API config for visibility
          const apiConfig = apiLayerConfigs.find((api: any) => api.layerName === layerConfig.apiName);
          const defaultVisible = apiConfig?.defaultVisible || false;
          
          const layerState: LayerState = {
            id: Date.now() + index,
            name: layerConfig.name,
            data: { type: 'FeatureCollection', features: [] },
            visible: defaultVisible, // Use dynamic visibility from API
            color: layerConfig.color,
            loading: layerConfig.type === 'geojson',
            type: layerConfig.type || 'geojson',
            wmsConfig: layerConfig.wmsConfig,
            style: apiConfig ? {
              pointColor: apiConfig.style.pointColor,
              pointRadius: apiConfig.style.pointRadius,
              pointOpacity: apiConfig.style.pointOpacity,
              pointFillOpacity: apiConfig.style.pointFillOpacity,
              lineColor: apiConfig.style.lineColor,
              lineWeight: apiConfig.style.lineWeight,
              lineOpacity: apiConfig.style.lineOpacity,
              polygonColor: apiConfig.style.polygonColor,
              polygonWeight: apiConfig.style.polygonWeight,
              polygonOpacity: apiConfig.style.polygonOpacity,
              polygonFillColor: apiConfig.style.polygonFillColor,
              polygonFillOpacity: apiConfig.style.polygonFillOpacity,
            } : undefined,
          };

          // Only load data for GeoJSON layers
          if (layerConfig.type === 'wms') {
            return { ...layerState, loading: false };
          }

          try {
            const data = await gisService.getLayer(layerConfig.apiName);
            return { ...layerState, data, loading: false };
          } catch (error) {
            console.error(`Error loading layer ${layerConfig.name}:`, error);
            return {
              ...layerState,
              loading: false,
              error: `Failed to load ${layerConfig.name}`
            };
          }
        });

        const loadedLayers = await Promise.all(layerPromises);
        setLayers(loadedLayers);
      } catch (error) {
        console.error('Failed to load layer configurations:', error);
        handleError(error);
        
        // Fallback to minimal WMS layers if API fails
        console.warn('API failed, loading only WMS layers as fallback');
        setLayerConfigs(WMS_LAYERS);
        
        const fallbackLayerStates = WMS_LAYERS.map((layerConfig, index) => ({
          id: Date.now() + index,
          name: layerConfig.name,
          data: { type: 'FeatureCollection' as const, features: [] },
          visible: false, // WMS layers hidden by default in fallback
          color: layerConfig.color,
          loading: false,
          type: layerConfig.type || 'geojson' as const,
          wmsConfig: layerConfig.wmsConfig,
        }));

        setLayers(fallbackLayerStates);
      } finally {
        setIsLoading(false);
      }
    };

    loadLayerConfigurations();
  }, []); // Empty dependency array - only run once on mount

  const toggleLayerVisibility = useCallback((layerId: number) => {
    setLayers(prevLayers => {
      const targetLayer = prevLayers.find(layer => layer.id === layerId);
      if (!targetLayer) return prevLayers;

      // Check if this is a GPZ layer
      const isGPZLayer = targetLayer.name.includes('GPZ');
      
      return prevLayers.map(layer => {
        if (layer.id === layerId) {
          // Toggle the clicked layer
          return { ...layer, visible: !layer.visible };
        } else if (isGPZLayer && layer.name.includes('GPZ') && layer.id !== layerId) {
          // If we're enabling a GPZ layer, disable other GPZ layers
          return targetLayer.visible ? layer : { ...layer, visible: false };
        } else {
          // Keep other layers unchanged
          return layer;
        }
      });
    });
  }, []);

  const refreshLayer = useCallback(async (id: number) => {
    const layer = layers.find(l => l.id === id);
    if (!layer) return;

    // Find the original layer config to get the API name
    const layerConfig = layerConfigs.find(config => config.name === layer.name);
    if (!layerConfig) return;

    // Only refresh GeoJSON layers
    if (layerConfig.type === 'wms') return;

    // Set loading state
    setLayers(prevLayers =>
      prevLayers.map(l =>
        l.id === id ? { ...l, loading: true, error: undefined } : l
      )
    );

    try {
      const gisService = getGISService();
      const data = await gisService.getLayer(layerConfig.apiName);

      setLayers(prevLayers =>
        prevLayers.map(l =>
          l.id === id ? { ...l, data, loading: false } : l
        )
      );
    } catch (error) {
      console.error(`Error refreshing layer ${layer.name}:`, error);
      setLayers(prevLayers =>
        prevLayers.map(l =>
          l.id === id 
            ? { ...l, loading: false, error: `Failed to refresh ${layer.name}` }
            : l
        )
      );
    }
  }, [layers, layerConfigs]);

  const addLayer = useCallback(async (config: LayerConfig) => {
    const newId = Date.now();
    
    const newLayer: LayerState = {
      id: newId,
      name: config.name,
      data: { type: 'FeatureCollection', features: [] },
      visible: true,
      color: config.color,
      loading: config.type === 'geojson',
      type: config.type || 'geojson',
      wmsConfig: config.wmsConfig,
    };

    // Add layer to state immediately
    setLayers(prevLayers => [...prevLayers, newLayer]);

    // Load data for GeoJSON layers
    if (config.type !== 'wms') {
      try {
        const gisService = getGISService();
        const data = await gisService.getLayer(config.apiName);

        setLayers(prevLayers =>
          prevLayers.map(layer =>
            layer.id === newId ? { ...layer, data, loading: false } : layer
          )
        );
      } catch (error) {
        console.error(`Error loading new layer ${config.name}:`, error);
        setLayers(prevLayers =>
          prevLayers.map(layer =>
            layer.id === newId 
              ? { ...layer, loading: false, error: `Failed to load ${config.name}` }
              : layer
          )
        );
      }
    }
  }, []);

  const removeLayer = useCallback((layerId: number) => {
    setLayers(prevLayers => prevLayers.filter(layer => layer.id !== layerId));
  }, []);

  return {
    layers,
    queryResult,
    isLoading,
    error,
    toggleLayerVisibility,
    refreshLayer,
    addLayer,
    removeLayer,
    setQueryResult,
    clearError,
  };
};