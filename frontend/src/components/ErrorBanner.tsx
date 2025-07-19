/**
 * Error banner component for displaying application errors
 */

import React from 'react';
import type { ErrorBannerProps } from '../types/components';

const ErrorBanner: React.FC<ErrorBannerProps> = ({ 
  error, 
  onDismiss, 
  type = 'error',
  className = '' 
}) => {
  if (!error) return null;

  const getTypeStyles = () => {
    switch (type) {
      case 'warning':
        return {
          backgroundColor: '#fff3cd',
          color: '#856404',
          borderColor: '#ffeaa7'
        };
      case 'info':
        return {
          backgroundColor: '#d1ecf1',
          color: '#0c5460',
          borderColor: '#bee5eb'
        };
      case 'error':
      default:
        return {
          backgroundColor: '#f8d7da',
          color: '#721c24',
          borderColor: '#f5c6cb'
        };
    }
  };

  const typeStyles = getTypeStyles();

  return (
    <div 
      className={`error-banner ${className}`}
      style={{
        ...typeStyles,
        padding: '12px 16px',
        border: `1px solid ${typeStyles.borderColor}`,
        borderRadius: '4px',
        margin: '8px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: '14px',
        lineHeight: '1.4'
      }}
      role="alert"
    >
      <span>{error}</span>
      {onDismiss && (
        <button
          onClick={onDismiss}
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            cursor: 'pointer',
            fontSize: '18px',
            fontWeight: 'bold',
            marginLeft: '12px',
            padding: '0 4px'
          }}
          aria-label="Zamknij komunikat o błędzie"
        >
          ×
        </button>
      )}
    </div>
  );
};

export default ErrorBanner;