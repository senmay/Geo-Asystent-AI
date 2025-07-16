
import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const GeoJsonLayer = ({ data, color }: { data: any, color?: string }) => {
  const map = useMap();
  const layerRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => {
    // Create layer
    if (data) {
      const geoJsonLayer = L.geoJSON(data, {
        style: () => ({
          color: color || `#${Math.floor(Math.random()*16777215).toString(16)}`, // Use prop color or random
          weight: 2,
          opacity: 0.8,
          fillOpacity: 0.2,
        }),
      }).addTo(map);

      layerRef.current = geoJsonLayer;

      const bounds = geoJsonLayer.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds);
      }
    }

    // Cleanup function to remove layer on component unmount
    return () => {
      if (layerRef.current) {
        layerRef.current.remove();
      }
    };
  }, [data, map, color]); // Add color to dependency array

  return null; // This component does not render any visible DOM element itself
};

export default GeoJsonLayer;
