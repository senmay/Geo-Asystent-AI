import React from 'react';
import { useMap } from 'react-leaflet';

export interface ZoomControlProps {
  className?: string;
}

const ZoomControl: React.FC<ZoomControlProps> = ({ className = '' }) => {
  const map = useMap();

  const handleZoomIn = () => {
    map.zoomIn();
  };

  const handleZoomOut = () => {
    map.zoomOut();
  };

  const handleControlClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    <div 
      className={`zoom-control ${className}`}
      onClick={handleControlClick}
      style={{
        position: 'absolute',
        top: '10px',
        right: '10px',
        zIndex: 1000,
        display: 'flex',
        flexDirection: 'column',
        gap: '2px',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        backdropFilter: 'blur(4px)',
        overflow: 'hidden'
      }}
    >
      <button
        onClick={handleZoomIn}
        style={{
          width: '40px',
          height: '40px',
          border: 'none',
          backgroundColor: 'transparent',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
          fontWeight: 'bold',
          color: '#333',
          transition: 'all 0.2s ease',
          borderBottom: '1px solid #e0e0e0'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#f0f0f0';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
        }}
        title="Przybliż"
      >
        +
      </button>
      <button
        onClick={handleZoomOut}
        style={{
          width: '40px',
          height: '40px',
          border: 'none',
          backgroundColor: 'transparent',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '18px',
          fontWeight: 'bold',
          color: '#333',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#f0f0f0';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
        }}
        title="Oddal"
      >
        −
      </button>
    </div>
  );
};

export default ZoomControl;