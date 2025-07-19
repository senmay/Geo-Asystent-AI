/**
 * Error handling service for consistent error management
 */

import type { ApiError } from './api/types';

export interface ErrorInfo {
  message: string;
  type: 'network' | 'server' | 'client' | 'validation' | 'unknown';
  code?: string;
  details?: any;
  timestamp: Date;
}

export class ErrorService {
  private static instance: ErrorService;
  private errorHandlers: Map<string, (error: ErrorInfo) => void> = new Map();

  static getInstance(): ErrorService {
    if (!ErrorService.instance) {
      ErrorService.instance = new ErrorService();
    }
    return ErrorService.instance;
  }

  /**
   * Process API error and convert to user-friendly format
   */
  processApiError(error: ApiError): ErrorInfo {
    let type: ErrorInfo['type'] = 'unknown';
    let message = 'Wystąpił nieoczekiwany błąd.';

    if (error.code === 'NETWORK_ERROR') {
      type = 'network';
      message = 'Brak połączenia z serwerem. Sprawdź połączenie internetowe.';
    } else if (error.status) {
      if (error.status >= 400 && error.status < 500) {
        type = 'client';
        if (error.status === 404) {
          message = 'Nie znaleziono żądanego zasobu.';
        } else if (error.status === 400) {
          message = 'Nieprawidłowe żądanie. Sprawdź wprowadzone dane.';
        } else if (error.status === 401) {
          message = 'Brak autoryzacji. Zaloguj się ponownie.';
        } else if (error.status === 403) {
          message = 'Brak uprawnień do wykonania tej operacji.';
        } else {
          message = error.message || 'Błąd po stronie klienta.';
        }
      } else if (error.status >= 500) {
        type = 'server';
        message = 'Błąd serwera. Spróbuj ponownie za chwilę.';
      }
    } else if (error.message) {
      message = error.message;
    }

    const errorInfo: ErrorInfo = {
      message,
      type,
      code: error.code,
      details: error.details,
      timestamp: new Date(),
    };

    // Log error for debugging
    console.error('🚨 Error processed:', errorInfo);

    // Notify registered handlers
    this.notifyHandlers(errorInfo);

    return errorInfo;
  }

  /**
   * Register error handler for specific error types
   */
  registerHandler(type: string, handler: (error: ErrorInfo) => void): void {
    this.errorHandlers.set(type, handler);
  }

  /**
   * Unregister error handler
   */
  unregisterHandler(type: string): void {
    this.errorHandlers.delete(type);
  }

  /**
   * Notify all registered handlers
   */
  private notifyHandlers(error: ErrorInfo): void {
    // Notify specific type handler
    const typeHandler = this.errorHandlers.get(error.type);
    if (typeHandler) {
      typeHandler(error);
    }

    // Notify global handler
    const globalHandler = this.errorHandlers.get('*');
    if (globalHandler) {
      globalHandler(error);
    }
  }

  /**
   * Create user-friendly error message for display
   */
  getDisplayMessage(error: ErrorInfo): string {
    return error.message;
  }

  /**
   * Check if error should be retried
   */
  shouldRetry(error: ErrorInfo): boolean {
    return error.type === 'network' || (error.type === 'server' && !error.code);
  }

  /**
   * Get error severity level
   */
  getSeverity(error: ErrorInfo): 'low' | 'medium' | 'high' | 'critical' {
    switch (error.type) {
      case 'network':
        return 'medium';
      case 'server':
        return 'high';
      case 'client':
        return 'low';
      case 'validation':
        return 'low';
      default:
        return 'medium';
    }
  }
}

// Export singleton instance
export const errorService = ErrorService.getInstance();