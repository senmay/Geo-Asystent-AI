import L from 'leaflet';
import type { PointStyleOptions, PathStyleOptions } from './types/components';

// --- Point Styles ---
// Defines the appearance of circle markers for different layers.

const defaultPointStyle: PointStyleOptions = {
    radius: 6,
    fillColor: "#ff7800", // orange
    color: "#000",
    weight: 1,
    opacity: 1,
    fillOpacity: 0.8
};

const gpzPointStyle: PointStyleOptions = {
    radius: 8,
    fillColor: "#ff0000", // red
    color: "#fff", // white border for contrast
    weight: 2,
    opacity: 1,
    fillOpacity: 0.9
};

export const highlightPointStyle: PointStyleOptions = {
    radius: 10,
    fillColor: "#00FFFF", // Cyan for high visibility
    color: "#000",
    weight: 3,
    opacity: 1,
    fillOpacity: 1
};

export const getPointStyle = (layerName?: string): PointStyleOptions => {
    switch (layerName) {
        case 'GPZ 110kV':
            return gpzPointStyle;
        default:
            return defaultPointStyle;
    }
};

// Helper function to create a marker with the correct style
export const createStyledCircleMarker = (latlng: L.LatLng, layerName?: string): L.CircleMarker => {
    const style = getPointStyle(layerName);
    return L.circleMarker(latlng, { ...style, radius: style.radius ?? 8 });
};

// --- Line and Polygon Styles ---
// Defines the appearance of lines and polygons.

const defaultPathStyle: PathStyleOptions = {
    color: "#3388ff", // leaflet blue
    weight: 3,
    opacity: 0.7,
    fillOpacity: 0.2,
};

const parcelsPathStyle: PathStyleOptions = {
    color: "#00ff00", // green
    weight: 1,
    opacity: 1,
    fillOpacity: 0.1,
};

export const getPathStyle = (layerName?: string): PathStyleOptions => {
    switch (layerName) {
        case 'parcels':
            return parcelsPathStyle;
        default:
            return defaultPathStyle;
    }
};
