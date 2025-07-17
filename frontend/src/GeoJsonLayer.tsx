import { useEffect } from 'react';
import { useMap, GeoJSON, CircleMarker, Tooltip } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-markercluster';
import L from 'leaflet';
import { getPathStyle, getPointStyle, highlightPointStyle } from './mapStyles';

interface GeoJsonFeature {
  type: 'Feature';
  geometry: {
    type: string;
    coordinates: number[];
  };
  properties?: {
    name?: string;
    [key: string]: any;
  };
}

interface GeoJsonData {
  type: 'FeatureCollection';
  features: GeoJsonFeature[];
}

interface GeoJsonLayerProps {
  data: GeoJsonData;
  layerName?: string;
}

const GeoJsonLayer = ({ data, layerName }: GeoJsonLayerProps) => {
  const map = useMap();

  // Rozdzielamy dane
  const points = data.features.filter(f => f.geometry.type === 'Point');
  const others =   data.features.filter(f => f.geometry.type !== 'Point');

  // FitBounds na wszystkie geometrie (punkty + inne)
  useEffect(() => {
    const all = L.featureGroup([
      L.geoJSON(others),
      L.featureGroup(points.map(f =>
        L.circleMarker(
          [f.geometry.coordinates[1], f.geometry.coordinates[0]],
          getPointStyle(layerName)
        )
      ))
    ]);
    if (all.getBounds().isValid()) {
      map.fitBounds(all.getBounds());
    }
  }, [points, others, map, layerName]);

  return (
    <>
      {/* 1. Linie i poligony */}
      {others.length > 0 && (
        <GeoJSON
          data={others}
          style={() => getPathStyle(layerName)}
        />
      )}

      {/* 2. Punkty z klastrowaniem */}
      {points.length > 0 && (
        <MarkerClusterGroup>
          {points.map((f, i) => {
            const pos: L.LatLngExpression = [f.geometry.coordinates[1], f.geometry.coordinates[0]];
            const style = getPointStyle(layerName);
            return (
              <CircleMarker
                key={i}
                center={pos}
                radius={style.radius ?? 8}
                pathOptions={style}
                eventHandlers={{
                  mouseover: (e) => e.target.setStyle(highlightPointStyle).bringToFront(),
                  mouseout:  (e) => e.target.setStyle(style),
                }}
              >
                {f.properties?.name && <Tooltip>{f.properties.name}</Tooltip>}
              </CircleMarker>
            );
          })}
        </MarkerClusterGroup>
      )}
    </>
  );
};

export default GeoJsonLayer;
