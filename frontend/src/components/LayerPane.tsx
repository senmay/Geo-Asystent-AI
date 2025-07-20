import React, { useState } from 'react';
import type { LayerState } from '../hooks/useMapLayers';
import type { BasemapOption } from './BasemapControl';

export interface LayerPaneProps {
  layers: LayerState[];
  onToggleLayer: (id: number) => void;
  basemaps: BasemapOption[];
  activeBasemap: string;
  onBasemapChange: (basemapId: string) => void;
  className?: string;
}

const LayerPane: React.FC<LayerPaneProps> = ({
  layers,
  onToggleLayer,
  basemaps,
  activeBasemap,
  onBasemapChange,
  className = ''
}) => {
  const [isOpen, setIsOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<'layers' | 'basemaps'>('layers');

  const handlePaneClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  const visibleLayers = layers.filter(layer => !layer.error);
  const errorLayers = layers.filter(layer => layer.error);
  const geoJsonLayers = visibleLayers.filter(layer => layer.type !== 'wms');
  const wmsLayers = visibleLayers.filter(layer => layer.type === 'wms');

  const activeBasemapName = basemaps.find(b => b.id === activeBasemap)?.name || 'OpenStreetMap';

  return (
    <div
      className={`layer-pane ${className}`}
      onClick={handlePaneClick}
      style={{
        position: 'fixed',
        left: isOpen ? '0' : '-280px',
        top: '0',
        width: '300px',
        height: '100vh',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderRight: '2px solid rgba(0, 0, 0, 0.1)',
        boxShadow: '2px 0 8px rgba(0, 0, 0, 0.15)',
        backdropFilter: 'blur(4px)',
        zIndex: 1000,
        transition: 'left 0.3s ease-in-out',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}
    >
      {/* Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'absolute',
          right: '-40px',
          top: '20px',
          width: '40px',
          height: '40px',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          border: '2px solid rgba(0, 0, 0, 0.1)',
          borderLeft: 'none',
          borderRadius: '0 8px 8px 0',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '16px',
          color: '#333',
          boxShadow: '2px 0 8px rgba(0, 0, 0, 0.15)',
          transition: 'all 0.2s ease'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#f0f0f0';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.95)';
        }}
      >
        {isOpen ? '◀' : '▶'}
      </button>

      {/* Header */}
      <div style={{
        padding: '20px 20px 10px 20px',
        borderBottom: '1px solid #e0e0e0',
        backgroundColor: '#f8f9fa'
      }}>
        <h3 style={{
          margin: '0 0 15px 0',
          fontSize: '18px',
          fontWeight: '600',
          color: '#2c3e50'
        }}>
          🗺️ Panel Warstw
        </h3>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          gap: '2px',
          backgroundColor: '#e9ecef',
          borderRadius: '6px',
          padding: '2px'
        }}>
          <button
            onClick={() => setActiveTab('layers')}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: 'none',
              borderRadius: '4px',
              fontSize: '13px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              backgroundColor: activeTab === 'layers' ? '#007bff' : 'transparent',
              color: activeTab === 'layers' ? 'white' : '#6c757d'
            }}
          >
            Warstwy ({visibleLayers.length})
          </button>
          <button
            onClick={() => setActiveTab('basemaps')}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: 'none',
              borderRadius: '4px',
              fontSize: '13px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              backgroundColor: activeTab === 'basemaps' ? '#007bff' : 'transparent',
              color: activeTab === 'basemaps' ? 'white' : '#6c757d'
            }}
          >
            Mapy podkładowe
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div style={{
        flex: 1,
        overflow: 'auto',
        padding: '15px 20px'
      }}>
        {activeTab === 'layers' && (
          <div className="layers-content">
            {/* GeoJSON Layers */}
            {geoJsonLayers.length > 0 && (
              <div className="layer-group" style={{ marginBottom: '20px' }}>
                <div style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#495057',
                  marginBottom: '12px',
                  paddingBottom: '6px',
                  borderBottom: '2px solid #007bff',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span>📊</span>
                  Warstwy lokalne ({geoJsonLayers.length})
                </div>
                {geoJsonLayers.map((layer) => (
                  <div key={layer.id} className="layer-item" style={{
                    marginBottom: '8px',
                    padding: '10px',
                    backgroundColor: layer.visible ? '#f8f9fa' : '#ffffff',
                    border: `1px solid ${layer.visible ? '#007bff' : '#e9ecef'}`,
                    borderRadius: '6px',
                    transition: 'all 0.2s ease'
                  }}>
                    <label
                      htmlFor={`layer-checkbox-${layer.id}`}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        cursor: layer.loading ? 'wait' : 'pointer',
                        opacity: layer.loading ? 0.6 : 1
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={layer.visible}
                        onChange={() => onToggleLayer(layer.id)}
                        id={`layer-checkbox-${layer.id}`}
                        disabled={layer.loading}
                        style={{ transform: 'scale(1.2)' }}
                      />
                      {layer.color && (
                        <span
                          className="color-swatch"
                          style={{
                            backgroundColor: layer.color,
                            width: '16px',
                            height: '16px',
                            borderRadius: '3px',
                            display: 'inline-block',
                            border: '1px solid #ccc'
                          }}
                        />
                      )}
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: '13px',
                          fontWeight: '500',
                          color: '#212529'
                        }}>
                          {layer.name}
                        </div>
                        {layer.loading && (
                          <div style={{
                            fontSize: '11px',
                            color: '#6c757d',
                            fontStyle: 'italic',
                            marginTop: '2px'
                          }}>
                            Ładowanie...
                          </div>
                        )}
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            )}

            {/* WMS Layers */}
            {wmsLayers.length > 0 && (
              <div className="layer-group" style={{ marginBottom: '20px' }}>
                <div style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#495057',
                  marginBottom: '12px',
                  paddingBottom: '6px',
                  borderBottom: '2px solid #28a745',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span>🌐</span>
                  Warstwy WMS ({wmsLayers.length})
                </div>
                {wmsLayers.map((layer) => (
                  <div key={layer.id} className="layer-item" style={{
                    marginBottom: '8px',
                    padding: '10px',
                    backgroundColor: layer.visible ? '#f8f9fa' : '#ffffff',
                    border: `1px solid ${layer.visible ? '#28a745' : '#e9ecef'}`,
                    borderRadius: '6px',
                    transition: 'all 0.2s ease'
                  }}>
                    <label
                      htmlFor={`layer-checkbox-${layer.id}`}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        cursor: layer.loading ? 'wait' : 'pointer',
                        opacity: layer.loading ? 0.6 : 1
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={layer.visible}
                        onChange={() => onToggleLayer(layer.id)}
                        id={`layer-checkbox-${layer.id}`}
                        disabled={layer.loading}
                        style={{ transform: 'scale(1.2)' }}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: '13px',
                          fontWeight: '500',
                          color: '#212529'
                        }}>
                          {layer.name}
                        </div>
                        <div style={{
                          fontSize: '10px',
                          color: '#6c757d',
                          fontStyle: 'italic',
                          marginTop: '2px'
                        }}>
                          WMS • Kliknij na mapę dla info
                        </div>
                      </div>
                    </label>
                  </div>
                ))}
              </div>
            )}

            {/* Error layers */}
            {errorLayers.length > 0 && (
              <div className="layer-errors" style={{ marginTop: '20px' }}>
                <div style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: '#dc3545',
                  marginBottom: '12px',
                  paddingBottom: '6px',
                  borderBottom: '2px solid #dc3545',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span>⚠️</span>
                  Błędy ładowania ({errorLayers.length})
                </div>
                {errorLayers.map((layer) => (
                  <div
                    key={layer.id}
                    style={{
                      fontSize: '12px',
                      color: '#6c757d',
                      marginBottom: '6px',
                      padding: '8px',
                      backgroundColor: '#f8d7da',
                      border: '1px solid #f5c6cb',
                      borderRadius: '4px'
                    }}
                  >
                    <strong>{layer.name}:</strong> {layer.error}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'basemaps' && (
          <div className="basemaps-content">
            <div style={{
              fontSize: '13px',
              color: '#6c757d',
              marginBottom: '15px',
              padding: '10px',
              backgroundColor: '#e7f3ff',
              border: '1px solid #b3d9ff',
              borderRadius: '6px'
            }}>
              <strong>Aktywna:</strong> {activeBasemapName}
            </div>

            {basemaps.map((basemap) => (
              <div key={basemap.id} className="basemap-item" style={{
                marginBottom: '8px',
                padding: '12px',
                backgroundColor: basemap.id === activeBasemap ? '#e7f3ff' : '#ffffff',
                border: `1px solid ${basemap.id === activeBasemap ? '#007bff' : '#e9ecef'}`,
                borderRadius: '6px',
                transition: 'all 0.2s ease'
              }}>
                <label
                  htmlFor={`basemap-radio-${basemap.id}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    cursor: 'pointer'
                  }}
                >
                  <input
                    type="radio"
                    checked={basemap.id === activeBasemap}
                    onChange={() => onBasemapChange(basemap.id)}
                    id={`basemap-radio-${basemap.id}`}
                    name="basemap"
                    style={{ transform: 'scale(1.2)' }}
                  />
                  <div style={{ flex: 1 }}>
                    <div style={{
                      fontSize: '13px',
                      fontWeight: basemap.id === activeBasemap ? '600' : '500',
                      color: basemap.id === activeBasemap ? '#007bff' : '#212529'
                    }}>
                      {basemap.name}
                    </div>
                    {basemap.id === 'none' && (
                      <div style={{
                        fontSize: '11px',
                        color: '#6c757d',
                        fontStyle: 'italic',
                        marginTop: '2px'
                      }}>
                        Tylko warstwy bez podkładu
                      </div>
                    )}
                  </div>
                </label>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LayerPane;