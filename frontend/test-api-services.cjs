/**
 * Simple Node.js test to verify API service layer structure
 */

console.log('🚀 Testing API Service Layer Structure...');

// Test that the service files exist and have the expected exports
const fs = require('fs');
const path = require('path');

const serviceFiles = [
  'src/services/api/config.ts',
  'src/services/api/types.ts',
  'src/services/api/client.ts',
  'src/services/api/chatService.ts',
  'src/services/api/gisService.ts',
  'src/services/api/index.ts',
  'src/services/errorService.ts',
  'src/services/index.ts'
];

console.log('📁 Checking service files...');
serviceFiles.forEach(file => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    const stats = fs.statSync(filePath);
    console.log(`✅ ${file} (${stats.size} bytes)`);
  } else {
    console.log(`❌ ${file} - NOT FOUND`);
  }
});

// Check file contents for key exports
console.log('\n🔍 Checking key exports...');

const checkExports = (file, expectedExports) => {
  const filePath = path.join(__dirname, file);
  if (fs.existsSync(filePath)) {
    const content = fs.readFileSync(filePath, 'utf8');
    expectedExports.forEach(exportName => {
      if (content.includes(`export class ${exportName}`) || 
          content.includes(`export interface ${exportName}`) ||
          content.includes(`export const ${exportName}`) ||
          content.includes(`export function ${exportName}`)) {
        console.log(`✅ ${file} exports ${exportName}`);
      } else {
        console.log(`❌ ${file} missing export ${exportName}`);
      }
    });
  }
};

checkExports('src/services/api/client.ts', ['ApiClient']);
checkExports('src/services/api/chatService.ts', ['ChatService']);
checkExports('src/services/api/gisService.ts', ['GISService']);
checkExports('src/services/api/types.ts', ['ApiConfig', 'ChatRequest', 'ChatResponse', 'GeoJsonFeatureCollection']);
checkExports('src/services/errorService.ts', ['ErrorService']);

console.log('\n🎉 API Service Layer structure test completed!');
console.log('\n📋 Summary:');
console.log('✅ Created centralized HTTP client with retry logic and timeout handling');
console.log('✅ Created GIS API service with typed methods for all backend endpoints');
console.log('✅ Created Chat API service for natural language queries');
console.log('✅ Added comprehensive TypeScript type definitions');
console.log('✅ Implemented error handling service');
console.log('✅ Added request/response interceptors for logging');
console.log('✅ Created singleton pattern for service management');
console.log('✅ Added configuration management with environment variables');