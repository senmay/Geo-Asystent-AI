/**
 * Chat API service for natural language queries
 */

import { ApiClient } from './client';
import { API_ENDPOINTS } from './config';
import type {
  ChatRequest,
  ChatResponse,
  GeoJsonFeatureCollection,
  RequestOptions,
} from './types';

export interface ProcessedChatResponse {
  type: 'text' | 'geojson';
  content: string | GeoJsonFeatureCollection;
  intent: string;
  metadata?: Record<string, any>;
  rawResponse: ChatResponse;
}

export class ChatService {
  private apiClient: ApiClient;

  constructor(apiClient: ApiClient) {
    this.apiClient = apiClient;
  }

  /**
   * Send a chat message and get processed response
   */
  async sendMessage(
    query: string,
    context?: Record<string, any>,
    options?: RequestOptions
  ): Promise<ProcessedChatResponse> {
    const request: ChatRequest = {
      query,
      ...(context && { context }),
    };

    const response = await this.apiClient.post<ChatResponse>(
      API_ENDPOINTS.CHAT,
      request,
      {},
      options
    );

    return this.processResponse(response.data);
  }

  /**
   * Process raw chat response into typed format
   */
  private processResponse(response: ChatResponse): ProcessedChatResponse {
    let content: string | GeoJsonFeatureCollection;

    if (response.type === 'geojson') {
      try {
        content = JSON.parse(response.data) as GeoJsonFeatureCollection;
      } catch (error) {
        console.error('Failed to parse GeoJSON response:', error);
        // Fallback to text response
        return {
          type: 'text',
          content: 'Błąd podczas przetwarzania danych GeoJSON.',
          intent: response.intent,
          metadata: response.metadata,
          rawResponse: response,
        };
      }
    } else {
      content = response.data;
    }

    return {
      type: response.type,
      content,
      intent: response.intent,
      metadata: response.metadata,
      rawResponse: response,
    };
  }

  /**
   * Get friendly name for intent
   */
  getIntentDisplayName(intent: string): string {
    const intentNames: Record<string, string> = {
      get_gis_data: 'Pobieranie warstwy GIS',
      find_largest_parcel: 'Wyszukiwanie największej działki',
      find_n_largest_parcels: 'Wyszukiwanie N największych działek',
      find_parcels_above_area: 'Wyszukiwanie działek powyżej określonej powierzchni',
      find_parcels_near_gpz: 'Wyszukiwanie działek w pobliżu GPZ',
      chat: 'Rozmowa ogólna',
    };

    return intentNames[intent] || intent;
  }

  /**
   * Extract feature messages from GeoJSON response
   */
  extractFeatureMessages(geojson: GeoJsonFeatureCollection): string[] {
    return geojson.features
      .map(feature => feature.properties?.message)
      .filter((message): message is string => Boolean(message));
  }

  /**
   * Create summary message for GeoJSON response
   */
  createGeoJsonSummary(geojson: GeoJsonFeatureCollection): string {
    const featureCount = geojson.features?.length || 0;
    const messages = this.extractFeatureMessages(geojson);

    if (messages.length > 0) {
      return messages.join('\n');
    }

    return `Wyświetlono ${featureCount} obiektów na mapie.`;
  }

  /**
   * Validate query before sending
   */
  validateQuery(query: string): { isValid: boolean; error?: string } {
    if (!query || query.trim().length === 0) {
      return { isValid: false, error: 'Zapytanie nie może być puste.' };
    }

    if (query.length > 1000) {
      return { isValid: false, error: 'Zapytanie jest zbyt długie (maksymalnie 1000 znaków).' };
    }

    return { isValid: true };
  }
}