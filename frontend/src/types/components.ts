/**
 * TypeScript type definitions for React components
 */

import type { ReactNode, CSSProperties } from 'react';
import type { GeoJsonFeatureCollection } from '../services/api/types';
import type { LayerState } from '../hooks/useMapLayers';

// Base component props
export interface BaseComponentProps {
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
}

// App component types
export interface AppProps extends BaseComponentProps {}

// Chat component types
export interface ChatProps {
  setQueryGeojson: (geojson: GeoJsonFeatureCollection | null) => void;
}

export interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export interface ChatMessageProps {
  message: {
    sender: 'user' | 'bot';
    text: string;
    type?: 'info' | 'data';
  };
  className?: string;
}

export interface ChatHistoryProps {
  messages: Array<{
    sender: 'user' | 'bot';
    text: string;
    type?: 'info' | 'data';
  }>;
  isLoading?: boolean;
  loadingMessage?: string;
}

// Layer Control component types
export interface LayerControlProps {
  layers: LayerState[];
  onToggleLayer: (id: number) => void;
  className?: string;
}

export interface LayerItemProps {
  layer: LayerState;
  onToggle: () => void;
  className?: string;
}

// GeoJSON Layer component types
export interface GeoJsonLayerProps {
  data: GeoJsonFeatureCollection;
  layerName?: string;
  color?: string;
  style?: MapStyleOptions;
  onFeatureClick?: (feature: any, layer: any) => void;
  onFeatureHover?: (feature: any, layer: any) => void;
  fitBounds?: boolean;
}

// Map-related component types
export interface MapContainerProps extends BaseComponentProps {
  center: [number, number];
  zoom: number;
  minZoom?: number;
  maxZoom?: number;
  bounds?: [[number, number], [number, number]];
  onMapReady?: (map: any) => void;
}

// Error display component types
export interface ErrorBannerProps {
  error: string | null;
  onDismiss?: () => void;
  type?: 'error' | 'warning' | 'info';
  className?: string;
}

export interface ErrorMessageProps {
  message: string;
  details?: string;
  onRetry?: () => void;
  className?: string;
}

// Loading component types
export interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
  className?: string;
}

export interface LoadingOverlayProps extends BaseComponentProps {
  isLoading: boolean;
  message?: string;
  transparent?: boolean;
}

// Form component types
export interface FormProps extends BaseComponentProps {
  onSubmit: (event: React.FormEvent) => void;
}

export interface InputProps {
  type?: 'text' | 'email' | 'password' | 'number' | 'search';
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  className?: string;
}

export interface ButtonProps extends BaseComponentProps {
  type?: 'button' | 'submit' | 'reset';
  variant?: 'primary' | 'secondary' | 'danger' | 'success';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  loading?: boolean;
  onClick?: () => void;
}

// Map styling types
export interface MapStyleOptions {
  color?: string;
  weight?: number;
  opacity?: number;
  fillColor?: string;
  fillOpacity?: number;
  dashArray?: string;
  lineCap?: 'butt' | 'round' | 'square';
  lineJoin?: 'miter' | 'round' | 'bevel';
}

export interface PointStyleOptions extends MapStyleOptions {
  radius?: number;
}

export interface PathStyleOptions extends MapStyleOptions {
  smoothFactor?: number;
  noClip?: boolean;
}

// Event handler types
export type MapEventHandler = (event: any) => void;
export type LayerEventHandler = (layer: LayerState) => void;
export type FeatureEventHandler = (feature: any, layer: any) => void;
export type ErrorEventHandler = (error: Error | string) => void;