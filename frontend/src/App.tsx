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
          center={[52.237049, 21.017532]} 
          zoom={13} 
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          
          {/* Render visible layers */}
          {layers
            .filter(layer => layer.visible && !layer.loading && !layer.error)
            .map((layer) => (
              <GeoJsonLayer 
                key={layer.id} 
                data={layer.data} 
                layerName={layer.name}
                color={layer.color}
              />
            ))
          }
          
          {/* Render query results */}
          {queryResult && (
            <GeoJsonLayer 
              data={queryResult} 
              layerName="Query Results"
              color="#FF0000" 
            />
          )}
          
          <LayerControl 
            layers={layers} 
            onToggleLayer={toggleLayer} 
          />
        </MapContainer>
      </div>
      
      <Chat setQueryGeojson={setQueryResult} />
    </div>
  );
};

export default App;