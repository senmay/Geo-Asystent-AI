/**
 * Services module - exports all application services
 */

// API services
export * from './api';

// Error handling
export * from './errorService';

// Re-export commonly used services for convenience
export {
  getChatService,
  getGISService,
  getApiClient,
  initializeApiServices,
  updateApiConfig,
} from './api';