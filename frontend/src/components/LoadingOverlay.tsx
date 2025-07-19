/**
 * Loading overlay component for displaying loading states
 */

import React from 'react';
import type { LoadingOverlayProps } from '../types/components';

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ 
  isLoading, 
  message = 'Ładowanie...', 
  transparent = false,
  className = '',
  style 
}) => {
  if (!isLoading) return null;

  return (
    <div 
      className={`loading-overlay ${className}`}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: transparent ? 'rgba(255, 255, 255, 0.7)' : 'rgba(0, 0, 0, 0.5)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 9999,
        ...style
      }}
    >
      <div 
        className="loading-spinner"
        style={{
          width: '40px',
          height: '40px',
          border: '4px solid #f3f3f3',
          borderTop: '4px solid #3498db',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
          marginBottom: '16px'
        }}
      />
      <div 
        className="loading-message"
        style={{
          color: transparent ? '#333' : '#fff',
          fontSize: '16px',
          fontWeight: '500'
        }}
      >
        {message}
      </div>
      
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default LoadingOverlay;