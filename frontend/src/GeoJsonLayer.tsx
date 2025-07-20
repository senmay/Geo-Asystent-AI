import { useEffect } from 'react';
import { useMap, GeoJSON, CircleMarker, Tooltip } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-markercluster';
import L from 'leaflet';
import { getPathStyle, getPointStyle, highlightPointStyle } from './mapStyles';
import type { GeoJsonLayerProps } from './types/components';
import type { PointGeometry } from './types/map';

const GeoJsonLayer = ({ data, layerName, fitBounds = true }: GeoJsonLayerProps) => {
  const map = useMap();

  // Rozdzielamy dane
  const points = data.features.filter(f => f.geometry.type === 'Point');
  const others =   data.features.filter(f => f.geometry.type !== 'Point');

  // FitBounds na wszystkie geometrie (punkty + inne)
  useEffect(() => {
    if (!fitBounds) {
      return;
    }
    
    const all = L.featureGroup([
      L.geoJSON({ type: 'FeatureCollection', features: others } as any),
      L.featureGroup(points.map(f => {
        const pointGeom = f.geometry as PointGeometry;
        return L.circleMarker(
          [pointGeom.coordinates[1], pointGeom.coordinates[0]],
          { ...getPointStyle(layerName), radius: getPointStyle(layerName).radius ?? 8 }
        );
      }))
    ]);
    if (all.getBounds().isValid()) {
      map.fitBounds(all.getBounds());
    }
  }, [points, others, map, layerName, fitBounds]);

  const onEachFeature = (feature: any, layer: L.Layer) => {
    if (layerName === 'Województwa' && feature.properties && feature.properties.JPT_NAZWA_) {
      layer.bindTooltip(feature.properties.JPT_NAZWA_, { permanent: true, direction: 'center', className: 'wojewodztwo-label' });
    }
  };

  return (
    <>
      {/* 1. Linie i poligony */}
      {others.length > 0 && (
        <GeoJSON
          data={{ type: 'FeatureCollection', features: others } as any}
          style={() => getPathStyle(layerName)}
          onEachFeature={onEachFeature}
        />
      )}

      {/* 2. Punkty z klastrowaniem */}
      {points.length > 0 && (
        <MarkerClusterGroup
          zoomToBoundsOnClick={false}
        >
          {points.map((f, i) => {
            const pointGeom = f.geometry as PointGeometry;
            const pos: L.LatLngExpression = [pointGeom.coordinates[1], pointGeom.coordinates[0]];
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
