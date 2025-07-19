/**
 * Main API service module - exports all services and utilities
 */

import { ApiClient } from './client';
import { ChatService } from './chatService';
import { GISService } from './gisService';
import { defaultApiConfig } from './config';
import type { ApiConfig } from './types';

// Export types
export * from './types';
export * from './config';

// Export services
export { ApiClient } from './client';
export { ChatService } from './chatService';
export { GISService } from './gisService';

// Create singleton instances
let apiClient: ApiClient;
let chatService: ChatService;
let gisService: GISService;

/**
 * Initialize API services with optional configuration
 */
export function initializeApiServices(config: Partial<ApiConfig> = {}): void {
  apiClient = new ApiClient(config);
  chatService = new ChatService(apiClient);
  gisService = new GISService(apiClient);
}

/**
 * Get the API client instance
 */
export function getApiClient(): ApiClient {
  if (!apiClient) {
    initializeApiServices();
  }
  return apiClient;
}

/**
 * Get the chat service instance
 */
export function getChatService(): ChatService {
  if (!chatService) {
    initializeApiServices();
  }
  return chatService;
}

/**
 * Get the GIS service instance
 */
export function getGISService(): GISService {
  if (!gisService) {
    initializeApiServices();
  }
  return gisService;
}

/**
 * Update API configuration for all services
 */
export function updateApiConfig(config: Partial<ApiConfig>): void {
  if (apiClient) {
    apiClient.updateConfig(config);
  } else {
    initializeApiServices(config);
  }
}

/**
 * Create a new API client with custom configuration
 */
export function createApiClient(config: Partial<ApiConfig> = {}): ApiClient {
  return new ApiClient(config);
}

/**
 * Create a new chat service with custom API client
 */
export function createChatService(client?: ApiClient): ChatService {
  return new ChatService(client || getApiClient());
}

/**
 * Create a new GIS service with custom API client
 */
export function createGISService(client?: ApiClient): GISService {
  return new GISService(client || getApiClient());
}

// Initialize with default configuration
initializeApiServices(defaultApiConfig);