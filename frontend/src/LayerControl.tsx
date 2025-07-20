import React, { useState } from 'react';
import type { LayerControlProps } from './types/components';
import './App.css';

const LayerControl: React.FC<LayerControlProps> = ({ 
  layers, 
  onToggleLayer, 
  className = '' 
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [position, setPosition] = useState({ x: 10, y: 10 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleControlClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget || (e.target as HTMLElement).classList.contains('layer-control-header')) {
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

  if (layers.length === 0) {
    return null;
  }

  const visibleLayers = layers.filter(layer => !layer.error);
  const errorLayers = layers.filter(layer => layer.error);
  
  // Group layers by type
  const geoJsonLayers = visibleLayers.filter(layer => layer.type !== 'wms');
  const wmsLayers = visibleLayers.filter(layer => layer.type === 'wms');

  return (
    <div 
      className={`layer-control ${className}`} 
      onClick={handleControlClick}
      onMouseDown={handleMouseDown}
      style={{
        position: 'absolute',
        left: position.x,
        top: position.y,
        zIndex: 1000,
        cursor: isDragging ? 'grabbing' : 'grab'
      }}
    >
      <h4 
        className="layer-control-header" 
        onClick={() => setIsOpen(!isOpen)}
        style={{ 
          cursor: 'pointer',
          userSelect: 'none',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        Warstwy ({visibleLayers.length})
        <span className="toggle-icon">{isOpen ? '▼' : '►'}</span>
      </h4>
      
      {isOpen && (
        <div className="layer-list" onClick={handleControlClick}>
          {/* GeoJSON Layers */}
          {geoJsonLayers.length > 0 && (
            <div className="layer-group">
              <div style={{ 
                fontSize: '13px', 
                fontWeight: '600', 
                color: '#333',
                marginBottom: '8px',
                paddingBottom: '4px',
                borderBottom: '1px solid #eee'
              }}>
                Warstwy lokalne ({geoJsonLayers.length})
              </div>
              {geoJsonLayers.map((layer) => (
                <div key={layer.id} className="layer-item">
                  <input
                    type="checkbox"
                    checked={layer.visible}
                    onChange={() => onToggleLayer(layer.id)}
                    id={`layer-checkbox-${layer.id}`}
                    disabled={layer.loading}
                  />
                  <label 
                    htmlFor={`layer-checkbox-${layer.id}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      opacity: layer.loading ? 0.6 : 1,
                      cursor: layer.loading ? 'wait' : 'pointer'
                    }}
                  >
                    {layer.color && (
                      <span
                        className="color-swatch"
                        style={{ 
                          backgroundColor: layer.color,
                          width: '12px',
                          height: '12px',
                          borderRadius: '2px',
                          display: 'inline-block'
                        }}
                      />
                    )}
                    <span>{layer.name}</span>
                    {layer.loading && (
                      <span 
                        style={{ 
                          fontSize: '12px', 
                          color: '#666',
                          fontStyle: 'italic'
                        }}
                      >
                        (ładowanie...)
                      </span>
                    )}
                  </label>
                </div>
              ))}
            </div>
          )}

          {/* WMS Layers */}
          {wmsLayers.length > 0 && (
            <div className="layer-group" style={{ marginTop: geoJsonLayers.length > 0 ? '16px' : '0' }}>
              <div style={{ 
                fontSize: '13px', 
                fontWeight: '600', 
                color: '#333',
                marginBottom: '8px',
                paddingBottom: '4px',
                borderBottom: '1px solid #eee'
              }}>
                Warstwy WMS ({wmsLayers.length})
              </div>
              {wmsLayers.map((layer) => (
                <div key={layer.id} className="layer-item">
                  <input
                    type="checkbox"
                    checked={layer.visible}
                    onChange={() => onToggleLayer(layer.id)}
                    id={`layer-checkbox-${layer.id}`}
                    disabled={layer.loading}
                  />
                  <label 
                    htmlFor={`layer-checkbox-${layer.id}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                      opacity: layer.loading ? 0.6 : 1,
                      cursor: layer.loading ? 'wait' : 'pointer'
                    }}
                  >
                    {layer.color && (
                      <span
                        className="color-swatch"
                        style={{ 
                          backgroundColor: layer.color,
                          width: '12px',
                          height: '12px',
                          borderRadius: '2px',
                          display: 'inline-block'
                        }}
                      />
                    )}
                    <span>{layer.name}</span>
                    <span 
                      style={{ 
                        fontSize: '10px', 
                        color: '#888',
                        fontStyle: 'italic',
                        marginLeft: 'auto'
                      }}
                    >
                      WMS
                    </span>
                    {layer.loading && (
                      <span 
                        style={{ 
                          fontSize: '12px', 
                          color: '#666',
                          fontStyle: 'italic'
                        }}
                      >
                        (ładowanie...)
                      </span>
                    )}
                  </label>
                </div>
              ))}
            </div>
          )}
          
          {/* Error layers */}
          {errorLayers.length > 0 && (
            <div className="layer-errors" style={{ marginTop: '16px' }}>
              <div 
                style={{ 
                  fontSize: '12px', 
                  color: '#d32f2f', 
                  fontWeight: '500',
                  marginBottom: '4px'
                }}
              >
                Błędy ładowania:
              </div>
              {errorLayers.map((layer) => (
                <div 
                  key={layer.id} 
                  className="layer-error-item"
                  style={{
                    fontSize: '11px',
                    color: '#666',
                    marginLeft: '16px',
                    marginBottom: '2px'
                  }}
                >
                  {layer.name}: {layer.error}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default LayerControl;