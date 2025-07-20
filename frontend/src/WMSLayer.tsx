import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

// Extend Leaflet types for WMS
declare module 'leaflet' {
  namespace TileLayer {
    class WMS extends TileLayer {
      constructor(baseUrl: string, options?: any);
    }
  }
  
  namespace tileLayer {
    function wms(baseUrl: string, options?: any): TileLayer.WMS;
  }
}

export interface WMSLayerProps {
  url: string;
  layers: string;
  name: string;
  visible: boolean;
  opacity?: number;
  format?: string;
  transparent?: boolean;
  crs?: L.CRS;
  maxZoom?: number;
  minZoom?: number;
  onFeatureInfo?: (info: any, latlng: L.LatLng) => void;
}

const WMSLayer: React.FC<WMSLayerProps> = ({
  url,
  layers,
  name,
  visible,
  opacity = 1,
  format = 'image/png',
  transparent = true,
  crs = L.CRS.EPSG3857,
  maxZoom = 20,
  minZoom = 0,
  onFeatureInfo
}) => {
  const map = useMap();
  const wmsLayerRef = useRef<L.TileLayer.WMS | null>(null);

  useEffect(() => {
    if (!map) return;

    // Create WMS layer
    const wmsLayer = L.tileLayer.wms(url, {
      layers,
      format,
      transparent,
      crs,
      opacity,
      maxZoom,
      minZoom,
      attribution: `WMS: ${name}`
    });

    wmsLayerRef.current = wmsLayer;

    // Add click handler for GetFeatureInfo
    const handleMapClick = (e: L.LeafletMouseEvent) => {
      if (!visible || !onFeatureInfo) return;

      const point = map.latLngToContainerPoint(e.latlng);
      const size = map.getSize();
      
      // Build GetFeatureInfo URL
      const params = new URLSearchParams({
        service: 'WMS',
        version: '1.1.1',
        request: 'GetFeatureInfo',
        layers,
        query_layers: layers,
        styles: '',
        bbox: map.getBounds().toBBoxString(),
        width: size.x.toString(),
        height: size.y.toString(),
        format,
        info_format: 'application/json',
        srs: 'EPSG:4326',
        x: Math.round(point.x).toString(),
        y: Math.round(point.y).toString(),
        feature_count: '10'
      });

      const getFeatureInfoUrl = `${url}?${params.toString()}`;

      // Fetch feature info
      fetch(getFeatureInfoUrl)
        .then(response => response.json())
        .then(data => {
          onFeatureInfo(data, e.latlng);
        })
        .catch(error => {
          console.error('GetFeatureInfo error:', error);
          // Try text format as fallback
          const textParams = new URLSearchParams(params);
          textParams.set('info_format', 'text/plain');
          const textUrl = `${url}?${textParams.toString()}`;
          
          fetch(textUrl)
            .then(response => response.text())
            .then(text => {
              onFeatureInfo({ text }, e.latlng);
            })
            .catch(err => console.error('GetFeatureInfo text fallback error:', err));
        });
    };

    if (visible) {
      map.addLayer(wmsLayer);
      if (onFeatureInfo) {
        map.on('click', handleMapClick);
      }
    }

    return () => {
      if (map.hasLayer(wmsLayer)) {
        map.removeLayer(wmsLayer);
      }
      if (onFeatureInfo) {
        map.off('click', handleMapClick);
      }
    };
  }, [map, url, layers, name, visible, opacity, format, transparent, crs, onFeatureInfo]);

  // Update layer visibility and opacity
  useEffect(() => {
    if (!wmsLayerRef.current || !map) return;

    if (visible && !map.hasLayer(wmsLayerRef.current)) {
      map.addLayer(wmsLayerRef.current);
    } else if (!visible && map.hasLayer(wmsLayerRef.current)) {
      map.removeLayer(wmsLayerRef.current);
    }

    wmsLayerRef.current.setOpacity(opacity);
  }, [map, visible, opacity]);

  return null; // This component doesn't render anything directly
};

export default WMSLayer;