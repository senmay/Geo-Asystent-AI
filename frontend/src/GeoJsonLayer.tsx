import { useEffect } from 'react';
import { useMap, GeoJSON, CircleMarker, Tooltip } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-markercluster';
import L from 'leaflet';
import { getPathStyle, getPointStyle, highlightPointStyle } from './mapStyles';
import type { GeoJsonLayerProps } from './types/components';
import type { PointGeometry } from './types/map';

const GeoJsonLayer = ({ data, layerName, style, fitBounds = true }: GeoJsonLayerProps) => {
  const map = useMap();

  // Convert API style to Leaflet style or use fallback
  const getLayerPathStyle = () => {
    if (style) {
      return {
        color: style.polygonColor || style.lineColor || "#3388ff",
        weight: style.lineWeight || 2,
        opacity: style.polygonOpacity || style.lineOpacity || 0.7,
        fillColor: style.polygonFillColor || style.polygonColor || "#3388ff",
        fillOpacity: style.polygonFillOpacity || 0.2,
      };
    }
    return getPathStyle(layerName); // Fallback to hardcoded styles
  };

  const getLayerPointStyle = () => {
    if (style) {
      return {
        radius: style.pointRadius || 6,
        fillColor: style.pointColor || "#ff7800",
        color: "#000",
        weight: 1,
        opacity: 1,
        fillOpacity: style.pointFillOpacity || 0.8
      };
    }
    return getPointStyle(layerName); // Fallback to hardcoded styles
  };

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
        const pointStyle = getLayerPointStyle();
        return L.circleMarker(
          [pointGeom.coordinates[1], pointGeom.coordinates[0]],
          { ...pointStyle, radius: pointStyle.radius ?? 8 }
        );
      }))
    ]);
    if (all.getBounds().isValid()) {
      map.fitBounds(all.getBounds());
    }
  }, [points, others, map, layerName, fitBounds]);

  const onEachFeature = (feature: any, layer: L.Layer) => {
    if (layerName === 'Województwa' && feature.properties && feature.properties.JPT_NAZWA_) {
      const tooltip = layer.bindTooltip(feature.properties.JPT_NAZWA_, { 
        permanent: true, 
        direction: 'center', 
        className: 'wojewodztwo-label' 
      });
      
      // Hide labels when zoom is greater than 8
      const updateLabelVisibility = () => {
        const currentZoom = map.getZoom();
        const tooltipElement = tooltip.getTooltip();
        if (tooltipElement) {
          if (currentZoom > 8) {
            tooltipElement.getElement()?.style.setProperty('display', 'none');
          } else {
            tooltipElement.getElement()?.style.setProperty('display', 'block');
          }
        }
      };
      
      // Update visibility on zoom change
      map.on('zoomend', updateLabelVisibility);
      
      // Set initial visibility
      setTimeout(updateLabelVisibility, 100);
    }
  };

  return (
    <>
      {/* 1. Linie i poligony */}
      {others.length > 0 && (
        <GeoJSON
          data={{ type: 'FeatureCollection', features: others } as any}
          style={() => getLayerPathStyle()}
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
            const pointStyle = getLayerPointStyle();
            return (
              <CircleMarker
                key={i}
                center={pos}
                radius={pointStyle.radius ?? 8}
                pathOptions={pointStyle}
                eventHandlers={{
                  mouseover: (e) => e.target.setStyle(highlightPointStyle).bringToFront(),
                  mouseout:  (e) => e.target.setStyle(pointStyle),
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
