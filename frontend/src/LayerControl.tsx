import React, { useState } from 'react';
import type { LayerControlProps } from './types/components';
import './App.css';

const LayerControl: React.FC<LayerControlProps> = ({ 
  layers, 
  onToggleLayer, 
  className = '' 
}) => {
  const [isOpen, setIsOpen] = useState(true);

  if (layers.length === 0) {
    return null;
  }

  const visibleLayers = layers.filter(layer => !layer.error);
  const errorLayers = layers.filter(layer => layer.error);

  return (
    <div className={`layer-control ${className}`}>
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
        <div className="layer-list">
          {/* Visible layers */}
          {visibleLayers.map((layer) => (
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
          
          {/* Error layers */}
          {errorLayers.length > 0 && (
            <div className="layer-errors">
              <div 
                style={{ 
                  fontSize: '12px', 
                  color: '#d32f2f', 
                  fontWeight: '500',
                  marginTop: '8px',
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