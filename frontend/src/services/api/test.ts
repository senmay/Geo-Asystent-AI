/**
 * Simple test script to verify API service layer functionality
 */

import { getChatService, getGISService, initializeApiServices } from './index';

// Initialize services
console.log('🚀 Initializing API services...');
initializeApiServices({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 10000,
  retryAttempts: 2,
  retryDelay: 500,
});

// Test services are available
const chatService = getChatService();
const gisService = getGISService();

console.log('✅ Chat service initialized:', !!chatService);
console.log('✅ GIS service initialized:', !!gisService);

// Test service methods exist
console.log('✅ Chat service methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(chatService)));
console.log('✅ GIS service methods:', Object.getOwnPropertyNames(Object.getPrototypeOf(gisService)));

console.log('🎉 API service layer test completed successfully!');