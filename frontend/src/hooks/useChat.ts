/**
 * Custom hook to manage chat state and API interactions
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { getChatService } from '../services';
import { useErrorHandler } from './useErrorHandler';
import type { GeoJsonFeatureCollection } from '../services/api/types';
import type { ProcessedChatResponse } from '../services/api/chatService';

export interface Message {
  sender: 'user' | 'bot';
  text: string;
  type?: 'info' | 'data';
}

export interface UseChatReturn {
  messages: Message[];
  sendMessage: (query: string) => Promise<void>;
  isLoading: boolean;
  clearMessages: () => void;
  error: string | null;
  clearError: () => void;
}

export const useChat = (
  onGeoJsonResult?: (geojson: GeoJsonFeatureCollection | null) => void
): UseChatReturn => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const isInitializedRef = useRef(false);
  const { error, handleError, clearError } = useErrorHandler();

  const addMessage = useCallback((message: Message) => {
    setMessages(prev => [...prev, message]);
  }, []);

  useEffect(() => {
    if (!isInitializedRef.current) {
      const welcomeMessage: Message = {
        sender: 'bot',
        text: `Cześć! Jestem Geo-Asystent AI - Twój asystent do pracy z danymi przestrzennymi.

Obecnie oferuje funkcjonalność:
• Wyszukiwanie 'n' najwiekszych dzialek
• Wyszukiwanie dzialek o określonej powierzchni
• Wyszukiwanie działek bez budynków
• Eksport danych do pdf

Przykładowe zapytania :
- "pokaż największą działkę"
- "pokaż 5 najwiekszych dzialek"
- "pokaż działki bez budynków"

Zadaj mi pytanie o dane GIS!`,
        type: 'info'
      };
      addMessage(welcomeMessage);
      isInitializedRef.current = true;
    }
  }, [addMessage]);

  const sendMessage = useCallback(async (query: string) => {
    if (!query.trim()) return;

    // Clear previous GeoJSON results
    onGeoJsonResult?.(null);

    // Add user message
    const userMessage: Message = { sender: 'user', text: query };
    addMessage(userMessage);

    setIsLoading(true);
    clearError();

    try {
      const chatService = getChatService();

      // Validate query
      const validation = chatService.validateQuery(query);
      if (!validation.isValid) {
        throw new Error(validation.error);
      }

      const response: ProcessedChatResponse = await chatService.sendMessage(query);

      // Add intent info message if available
      if (response.intent) {
        const intentDisplayName = chatService.getIntentDisplayName(response.intent);
        const infoMessage: Message = {
          sender: 'bot',
          text: `Używam narzędzia: "${intentDisplayName}"`,
          type: 'info',
        };
        addMessage(infoMessage);
      }

      // Handle response based on type
      if (response.type === 'geojson' && typeof response.content === 'object') {
        const geojsonData = response.content as GeoJsonFeatureCollection;

        // Set GeoJSON result for map display
        onGeoJsonResult?.(geojsonData);

        // Create summary message
        const summaryText = chatService.createGeoJsonSummary(geojsonData);
        const botMessage: Message = {
          sender: 'bot',
          text: summaryText,
          type: 'data'
        };
        addMessage(botMessage);
      } else {
        // Text response
        const botMessage: Message = {
          sender: 'bot',
          text: response.content as string,
          type: 'data'
        };
        addMessage(botMessage);
      }
    } catch (error) {
      handleError(error);
      const errorMessage: Message = {
        sender: 'bot',
        text: 'Wystąpił błąd podczas komunikacji z serwerem.',
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [addMessage, onGeoJsonResult, handleError, clearError]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    isInitializedRef.current = false;
    clearError();
  }, [clearError]);

  return {
    messages,
    sendMessage,
    isLoading,
    clearMessages,
    error,
    clearError,
  };
};