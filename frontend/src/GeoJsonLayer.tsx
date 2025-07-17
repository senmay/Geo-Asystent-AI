
import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.markercluster';

// Define the type for our GeoJSON data for better type safety
interface GeoJsonFeature {
  type: "Feature";
  properties: object;
  geometry: {
    type: "Point" | "LineString" | "Polygon" | "MultiLineString" | "MultiPolygon";
    coordinates: any;
  };
}

interface GeoJsonData {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
}

// Helper to create the point style
const createCircleMarker = (latlng: L.LatLng, color?: string) => {
  return L.circleMarker(latlng, {
    radius: 8,
    fillColor: color || "#ff0000ff",
    color: "#000000",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.8
  });
};

const GeoJsonLayer = ({ data, color }: { data: GeoJsonData, color?: string }) => {
  const map = useMap();
  const layerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!data || !data.features) return;

    // Separate features by geometry type
    const points = data.features.filter(f => f.geometry.type === 'Point');
    const otherGeometries = data.features.filter(f => f.geometry.type !== 'Point');

    // --- 1. Handle Point Features with Clustering ---
    const markerClusterGroup = L.markerClusterGroup();
    points.forEach(feature => {
      const latlng = L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0]);
      const marker = createCircleMarker(latlng, color);
      markerClusterGroup.addLayer(marker);
    });

    // --- 2. Handle Other Geometries (Lines, Polygons) ---
    const otherLayers = L.geoJSON(otherGeometries, {
      style: () => ({
        color: color || `#${Math.floor(Math.random() * 16777215).toString(16)}`,
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.2,
      }),
    });

    // --- 3. Combine all layers into a single group ---
    const combinedLayerGroup = L.featureGroup([markerClusterGroup, otherLayers]); 
    combinedLayerGroup.addTo(map);
    layerRef.current = combinedLayerGroup;

    // --- 4. Fit map to bounds ---
    if (combinedLayerGroup.getLayers().length > 0) {
      const bounds = combinedLayerGroup.getBounds();
      if (bounds.isValid()) {
        map.fitBounds(bounds);
      }
    }

    // --- 5. Cleanup ---
    return () => {
      if (layerRef.current) {
        layerRef.current.remove();
      }
    };
  }, [data, map, color]);

  return null;
};

export default GeoJsonLayer;
''