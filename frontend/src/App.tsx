import { useState, useCallback, useRef, useEffect } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import GeoJsonLayer from './GeoJsonLayer';
import LayerControl from './LayerControl';
import Chat from './Chat';
import { ErrorBanner, LoadingOverlay } from './components';
import { useMapLayers } from './hooks';
import type { AppProps } from './types/components';
import 'leaflet/dist/leaflet.css';
import './App.css';

const App: React.FC<AppProps> = ({ className, style }) => {
  const {
    layers,
    queryResult,
    toggleLayer,
    setQueryResult,
    error,
    isLoading,
    clearError
  } = useMapLayers();

  const [chatWidth, setChatWidth] = useState(400); // Initial width
  const isResizing = useRef(false);

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    isResizing.current = true;
    e.preventDefault();
  };

  const handleMouseUp = () => {
    isResizing.current = false;
  };

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (isResizing.current) {
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth > 300 && newWidth < 800) { // Min and max width
        setChatWidth(newWidth);
      }
    }
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [handleMouseMove]);

  return (
    <div className={`app-container ${className || ''}`} style={style}>
      <ErrorBanner 
        error={error} 
        onDismiss={clearError}
        type="error"
      />
      
      <LoadingOverlay isLoading={isLoading} message="Ładowanie warstw..." />
      
      <div className="map-pane">
        <MapContainer 
          center={[52.23, 21.01]} // Center of Poland
          zoom={6} 
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          {layers
            .filter(layer => layer.visible && !layer.loading && !layer.error)
            .map((layer) => (
              <GeoJsonLayer 
                key={layer.id} 
                data={layer.data} 
                layerName={layer.name}
                color={layer.color}
                fitBounds={false} 
              />
            ))
          }
          
          {queryResult && (
            <GeoJsonLayer 
              data={queryResult} 
              layerName="Query Results"
              color="#FF0000"
              fitBounds={true}
            />
          )}
          
          <LayerControl 
            layers={layers} 
            onToggleLayer={toggleLayer} 
          />
        </MapContainer>
      </div>
      
      <div className="chat-container" style={{ width: chatWidth }}>
        <div className="resizer" onMouseDown={handleMouseDown}></div>
        <Chat setQueryGeojson={setQueryResult} />
      </div>
    </div>
  );
};

export default App;