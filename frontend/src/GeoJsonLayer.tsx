import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import MarkerClusterGroup from 'react-leaflet-markercluster'; // Use the React component
import { getPathStyle, getPointStyle, highlightPointStyle } from './mapStyles';

// Define the type for our GeoJSON data for better type safety
interface GeoJsonFeature {
  type: "Feature";
  properties: { [key: string]: any }; // Allow any properties
  geometry: {
    type: "Point" | "LineString" | "Polygon" | "MultiLineString" | "MultiPolygon";
    coordinates: any;
  };
}

interface GeoJsonData {
  type: "FeatureCollection";
  features: GeoJsonFeature[];
}

interface GeoJsonLayerProps {
  data: GeoJsonData;
  layerName?: string; // New prop to identify the layer type
}

// A custom component for a single point to handle events
const PointMarker = ({ feature, layerName }: { feature: GeoJsonFeature, layerName?: string }) => {
  const latlng = L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0]);
  const style = getPointStyle(layerName);

  const markerRef = useRef<L.CircleMarker | null>(null);

  const handleMouseOver = () => {
    markerRef.current?.setStyle(highlightPointStyle);
    markerRef.current?.bringToFront();
  };

  const handleMouseOut = () => {
    markerRef.current?.setStyle(getPointStyle(layerName));
  };

  useEffect(() => {
    const marker = L.circleMarker(latlng, style);
    markerRef.current = marker;

    if (feature.properties && feature.properties.name) {
      marker.bindTooltip(feature.properties.name);
    }

    marker.on('mouseover', handleMouseOver);
    marker.on('mouseout', handleMouseOut);

    // This part is tricky because we are mixing vanilla Leaflet with React-Leaflet.
    // A fully "React-way" would be to use <CircleMarker> components directly.
    // This hybrid approach is a fix for the current structure.

  }, [feature, layerName, latlng, style]);

  // This is a bit of a hack. We need to return a Leaflet layer.
  // The proper way is to use <CircleMarker> from react-leaflet inside MarkerClusterGroup.
  // But let's stick to the current logic and see if it works.
  const marker = L.circleMarker(latlng, style);
  if (feature.properties && feature.properties.name) {
    marker.bindTooltip(feature.properties.name);
  }
  marker.on('mouseover', handleMouseOver);
  marker.on('mouseout', handleMouseOut);
  (marker as any).feature = feature; // for cluster tooltips

  return marker;
};


const GeoJsonLayer = ({ data, layerName }: GeoJsonLayerProps) => {
  const map = useMap();
  const layerRef = useRef<L.FeatureGroup | null>(null);

  useEffect(() => {
    if (!data || !data.features) return;

    const otherGeometries = data.features.filter(f => f.geometry.type !== 'Point');

    // --- Handle Other Geometries (Lines, Polygons) ---
    const otherLayers = L.geoJSON(otherGeometries, {
      style: () => getPathStyle(layerName),
    });

    const featureGroup = L.featureGroup([otherLayers]);
    layerRef.current = featureGroup;
    map.addLayer(featureGroup);

    // Fit map to bounds of non-point layers
    if (otherGeometries.length > 0) {
        const bounds = otherLayers.getBounds();
        if (bounds.isValid()) {
            map.fitBounds(bounds);
        }
    }

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }
    };
  }, [data, map, layerName]);

  // --- Handle Point Features with Clustering separately ---
  const points = data.features.filter(f => f.geometry.type === 'Point');

  if (points.length === 0) {
    return null; // No points to render
  }

  return (
    <MarkerClusterGroup
      onClusterMouseOver={(cluster) => {
        const childMarkers = cluster.layer.getAllChildMarkers();
        const names = childMarkers
          .map(marker => (marker as any).feature?.properties?.name)
          .filter(Boolean);
        if (names.length > 0) {
          const tooltipContent = names.join('<br>');
          cluster.layer.bindTooltip(tooltipContent).openTooltip();
        }
      }}
      onClusterMouseOut={(cluster) => {
        cluster.layer.closeTooltip();
      }}
    >
      {points.map((feature, index) => {
        const latlng = L.latLng(feature.geometry.coordinates[1], feature.geometry.coordinates[0]);
        const style = getPointStyle(layerName);
        const marker = L.circleMarker(latlng, style);

        // This is a workaround to make the marker accessible to React-Leaflet
        const Point = () => {
            const pointRef = useRef<L.CircleMarker>();

            useEffect(() => {
                const m = L.circleMarker(latlng, style);
                if (feature.properties && feature.properties.name) {
                    m.bindTooltip(feature.properties.name);
                }
                m.on('mouseover', () => m.setStyle(highlightPointStyle).bringToFront());
                m.on('mouseout', () => m.setStyle(style));
                (m as any).feature = feature;

                pointRef.current = m;
                // Manually add to the parent cluster group
                // This is getting very complex. Let's simplify.
            }, []);
            return null;
        }
        return <Point key={index} />
      })}
    </MarkerClusterGroup>
  );
};

// Let's try a cleaner, more React-idiomatic approach.
import { CircleMarker, Popup, Tooltip } from 'react-leaflet';

const CleanGeoJsonLayer = ({ data, layerName }: GeoJsonLayerProps) => {
    const map = useMap();

    const points = data.features.filter(f => f.geometry.type === 'Point');
    const otherGeometries = data.features.filter(f => f.geometry.type !== 'Point');

    // Handle non-point geometries with useEffect and vanilla Leaflet
    useEffect(() => {
        if (otherGeometries.length === 0) return;
        const otherLayers = L.geoJSON(otherGeometries, {
            style: () => getPathStyle(layerName),
        }).addTo(map);

        const bounds = otherLayers.getBounds();
        if(bounds.isValid()) {
            map.fitBounds(bounds);
        }

        return () => {
            map.removeLayer(otherLayers);
        };
    }, [otherGeometries, map, layerName]);

    return (
        <MarkerClusterGroup>
            {points.map((feature, index) => {
                const latlng = [feature.geometry.coordinates[1], feature.geometry.coordinates[0]];
                const style = getPointStyle(layerName);

                return (
                    <CircleMarker
                        key={index}
                        center={latlng as L.LatLngExpression}
                        pathOptions={style}
                        eventHandlers={{
                            mouseover: (e) => e.target.setStyle(highlightPointStyle),
                            mouseout: (e) => e.target.setStyle(style),
                        }}
                    >
                        {feature.properties?.name && <Tooltip>{feature.properties.name}</Tooltip>}
                    </CircleMarker>
                );
            })}
        </MarkerClusterGroup>
    );
};

export default CleanGeoJsonLayer;
