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

// createStyledCircleMarker removed - no longer used

// --- Line and Polygon Styles ---
// Defines the appearance of lines and polygons.

const defaultPathStyle: PathStyleOptions = {
    color: "#3388ff", // leaflet blue
    weight: 3,
    opacity: 0.7,
    fillOpacity: 0.2,
};

// parcelsPathStyle removed - no longer used

export const getPathStyle = (layerName?: string): PathStyleOptions => {
    switch (layerName) {
        case 'Działki przykładowe':
            return {
                color: "#00ff00", // green
                weight: 2,
                opacity: 0.8,
                fillOpacity: 0.1,
            };
        case 'Budynki przykładowe':
            return {
                color: "#3388ff", // blue
                weight: 1,
                opacity: 0.9,
                fillOpacity: 0.5,
            };
        case 'Natura 2000':
            return {
                color: "#008000", // dark green
                weight: 2,
                opacity: 0.7,
                fillOpacity: 0.3,
            };
        case 'Województwa':
            return {
                color: "#800080", // purple
                weight: 3,
                opacity: 0.8,
                fillOpacity: 0,
            };
        default:
            return defaultPathStyle;
    }
};
