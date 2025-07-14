import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const GeoJsonLayer = ({ data }: { data: any }) => {
  const map = useMap();
  const layerRef = useRef<L.GeoJSON | null>(null);

  // Remove old layer on component unmount or data change
  useEffect(() => {
    return () => {
      if (layerRef.current) {
        layerRef.current.remove();
      }
    };
  }, []);

  // Add new layer when data changes
  useEffect(() => {
    if (data) {
      // Remove previous layer if it exists
      if (layerRef.current) {
        layerRef.current.remove();
      }
      
      const geoJsonLayer = L.geoJSON(data, {
        style: () => ({
          color: '#ff7800',
          weight: 2,
          opacity: 0.8,
          fillColor: '#ff7800',
          fillOpacity: 0.2,
        }),
      }).addTo(map);
      
      layerRef.current = geoJsonLayer;
      
      // Zoom to the layer
      const bounds = geoJsonLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds);
      }
    }
  }, [data, map]);

  return null; // This component does not render any visible DOM element itself
};

export default GeoJsonLayer;
