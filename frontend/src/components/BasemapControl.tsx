import React, { useState } from 'react';

export interface BasemapOption {
  id: string;
  name: string;
  url: string;
  attribution: string;
  maxZoom?: number;
}

export interface BasemapControlProps {
  basemaps: BasemapOption[];
  activeBasemap: string;
  onBasemapChange: (basemapId: string) => void;
  className?: string;
}

const BasemapControl: React.FC<BasemapControlProps> = ({
  basemaps,
  activeBasemap,
  onBasemapChange,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ x: 10, y: 60 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget || (e.target as HTMLElement).classList.contains('basemap-control-header')) {
      setIsDragging(true);
      setDragStart({
        x: e.clientX - position.x,
        y: e.clientY - position.y
      });
      e.preventDefault();
    }
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      setPosition({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  React.useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      return () => {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging, dragStart]);

  const handleControlClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  const activeBasemapName = basemaps.find(b => b.id === activeBasemap)?.name || 'OpenStreetMap';

  return (
    <div 
      className={`basemap-control ${className}`}
      onClick={handleControlClick}
      onMouseDown={handleMouseDown}
      style={{
        position: 'absolute',
        left: position.x,
        top: position.y,
        zIndex: 1000,
        cursor: isDragging ? 'grabbing' : 'grab',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        border: '2px solid rgba(0, 0, 0, 0.2)',
        borderRadius: '6px',
        padding: '8px',
        minWidth: '180px',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        backdropFilter: 'blur(4px)'
      }}
    >
      <h4 
        className="basemap-control-header"
        onClick={() => setIsOpen(!isOpen)}
        style={{ 
          cursor: 'pointer',
          userSelect: 'none',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          margin: '0 0 8px 0',
          fontSize: '13px',
          fontWeight: '600',
          color: '#333'
        }}
      >
        Mapa podkładowa
        <span className="toggle-icon">{isOpen ? '▼' : '►'}</span>
      </h4>
      
      {isOpen && (
        <div className="basemap-list">
          <div style={{ 
            fontSize: '12px', 
            color: '#666',
            marginBottom: '8px',
            fontWeight: '500'
          }}>
            Aktywna: {activeBasemapName}
          </div>
          
          {basemaps.map((basemap) => (
            <div key={basemap.id} className="basemap-item" style={{ marginBottom: '4px' }}>
              <input
                type="radio"
                checked={basemap.id === activeBasemap}
                onChange={() => onBasemapChange(basemap.id)}
                id={`basemap-radio-${basemap.id}`}
                name="basemap"
                style={{ marginRight: '8px' }}
              />
              <label 
                htmlFor={`basemap-radio-${basemap.id}`}
                style={{
                  fontSize: '12px',
                  cursor: 'pointer',
                  color: basemap.id === activeBasemap ? '#007bff' : '#333',
                  fontWeight: basemap.id === activeBasemap ? '500' : 'normal'
                }}
              >
                {basemap.name}
              </label>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default BasemapControl;