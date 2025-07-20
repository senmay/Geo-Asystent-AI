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
}

export interface LayerConfig {
  name: string;
  apiName: string;
  color: string;
}

export interface UseMapLayersReturn {
  layers: LayerState[];
  queryResult: GeoJsonFeatureCollection | null;
  isLoading: boolean;
  error: string | null;
  toggleLayer: (id: number) => void;
  setQueryResult: (data: GeoJsonFeatureCollection | null) => void;
  refreshLayer: (id: number) => Promise<void>;
  addLayer: (config: LayerConfig) => Promise<void>;
  removeLayer: (id: number) => void;
  clearError: () => void;
}

const DEFAULT_LAYERS: LayerConfig[] = [
  { name: 'GPZ 110kV', apiName: 'gpz_POLSKA', color: '#ff0000' },
  { name: 'Budynki', apiName: 'buildings', color: '#3388ff' },
  { name: 'Działki', apiName: 'parcels', color: '#00ff00' },
  { name: 'GPZ Wielkopolskie', apiName: 'GPZ_WIELKOPOLSKIE', color: '#ff00ff' },
  { name: 'Województwa', apiName: 'wojewodztwa', color: '#800080' },
  { name: 'Natura 2000', apiName: 'natura2000', color: '#008000' }
];

export const useMapLayers = (
  initialLayers: LayerConfig[] = DEFAULT_LAYERS
): UseMapLayersReturn => {
  const [layers, setLayers] = useState<LayerState[]>([]);
  const [queryResult, setQueryResult] = useState<GeoJsonFeatureCollection | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { error, handleError, clearError } = useErrorHandler();

  // Load initial layers on mount
  useEffect(() => {
    const loadInitialLayers = async () => {
      if (initialLayers.length === 0) return;

      setIsLoading(true);
      clearError();

      try {
        const gisService = getGISService();
        const layerPromises = initialLayers.map(async (layerConfig, index) => {
          const layerState: LayerState = {
            id: Date.now() + index,
            name: layerConfig.name,
            data: { type: 'FeatureCollection', features: [] },
            visible: !['GPZ Wielkopolskie', 'Województwa', 'Natura 2000'].includes(layerConfig.name),
            color: layerConfig.color,
            loading: true,
          };

          try {
            const data = await gisService.getLayer(layerConfig.apiName, true);
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
        handleError(error);
      } finally {
        setIsLoading(false);
      }
    };

    loadInitialLayers();
  }, [initialLayers, handleError, clearError]);

  const toggleLayer = useCallback((id: number) => {
    setLayers(prevLayers => {
      const toggledLayer = prevLayers.find(l => l.id === id);
      if (!toggledLayer) return prevLayers;

      const isTogglingOn = !toggledLayer.visible;
      const toggledName = toggledLayer.name;

      return prevLayers.map(layer => {
        // The layer being toggled
        if (layer.id === id) {
          return { ...layer, visible: !layer.visible };
        }

        // If we are turning a GPZ layer on, turn the other one off.
        if (isTogglingOn) {
          if (toggledName === 'GPZ 110kV' && layer.name === 'GPZ Wielkopolskie') {
            return { ...layer, visible: false };
          }
          if (toggledName === 'GPZ Wielkopolskie' && layer.name === 'GPZ 110kV') {
            return { ...layer, visible: false };
          }
        }

        // Otherwise, return the layer as is.
        return layer;
      });
    });
  }, []);

  const refreshLayer = useCallback(async (id: number) => {
    const layer = layers.find(l => l.id === id);
    if (!layer) return;

    // Find the original layer config to get the API name
    const layerConfig = initialLayers.find(config => config.name === layer.name);
    if (!layerConfig) return;

    setLayers(prevLayers =>
      prevLayers.map(l =>
        l.id === id ? { ...l, loading: true, error: undefined } : l
      )
    );

    try {
      const gisService = getGISService();
      const data = await gisService.getLayer(layerConfig.apiName, true);
      
      setLayers(prevLayers =>
        prevLayers.map(l =>
          l.id === id ? { ...l, data, loading: false } : l
        )
      );
    } catch (error) {
      console.error(`Error refreshing layer ${layer.name}:`, error);
      setLayers(prevLayers =>
        prevLayers.map(l =>
          l.id === id ? { 
            ...l, 
            loading: false, 
            error: `Failed to refresh ${layer.name}` 
          } : l
        )
      );
    }
  }, [layers, initialLayers]);

  const addLayer = useCallback(async (config: LayerConfig) => {
    const newLayer: LayerState = {
      id: Date.now(),
      name: config.name,
      data: { type: 'FeatureCollection', features: [] },
      visible: true,
      color: config.color,
      loading: true,
    };

    setLayers(prevLayers => [...prevLayers, newLayer]);

    try {
      const gisService = getGISService();
      const data = await gisService.getLayer(config.apiName, true);
      
      setLayers(prevLayers =>
        prevLayers.map(layer =>
          layer.id === newLayer.id ? { ...layer, data, loading: false } : layer
        )
      );
    } catch (error) {
      console.error(`Error adding layer ${config.name}:`, error);
      setLayers(prevLayers =>
        prevLayers.map(layer =>
          layer.id === newLayer.id ? { 
            ...layer, 
            loading: false, 
            error: `Failed to load ${config.name}` 
          } : layer
        )
      );
    }
  }, []);

  const removeLayer = useCallback((id: number) => {
    setLayers(prevLayers => prevLayers.filter(layer => layer.id !== id));
  }, []);

  return {
    layers,
    queryResult,
    isLoading,
    error,
    toggleLayer,
    setQueryResult,
    refreshLayer,
    addLayer,
    removeLayer,
    clearError,
  };
};