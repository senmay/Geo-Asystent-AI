/**
 * API configuration and constants
 */

import type { ApiConfig } from './types';

// Default configuration
export const defaultApiConfig: ApiConfig = {
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  retryDelay: 1000, // 1 second
};

// API endpoints
export const API_ENDPOINTS = {
  CHAT: '/api/v1/chat',
  LAYERS: {
    BASE: '/api/v1/layers',
    BY_NAME: (name: string) => `/api/v1/layers/${name}`,
    STATISTICS: (name: string) => `/api/v1/layers/${name}/statistics`,
    VALIDATE: (name: string) => `/api/v1/layers/${name}/validate`,
  },
  ANALYSIS: {
    PARCEL_DISTRIBUTION: '/api/v1/analysis/parcel-distribution',
  },
} as const;