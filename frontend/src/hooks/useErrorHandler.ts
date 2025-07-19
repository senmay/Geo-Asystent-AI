/**
 * Custom hook for consistent error management across the application
 */

import { useState, useCallback } from 'react';

export interface UseErrorHandlerReturn {
  error: string | null;
  setError: (error: string | null) => void;
  handleError: (error: Error | any) => void;
  clearError: () => void;
  hasError: boolean;
}

export const useErrorHandler = (): UseErrorHandlerReturn => {
  const [error, setError] = useState<string | null>(null);

  const handleError = useCallback((error: Error | any) => {
    console.error('Error handled by useErrorHandler:', error);
    
    let errorMessage: string;
    
    if (error?.response?.data?.error?.message) {
      // API error with structured response
      errorMessage = error.response.data.error.message;
    } else if (error?.message) {
      // Standard Error object
      errorMessage = error.message;
    } else if (typeof error === 'string') {
      // String error
      errorMessage = error;
    } else {
      // Unknown error type
      errorMessage = 'Wystąpił nieoczekiwany błąd.';
    }

    setError(errorMessage);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    error,
    setError,
    handleError,
    clearError,
    hasError: error !== null,
  };
};