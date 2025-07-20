import { useState, useCallback, useRef, useEffect } from 'react';
import { MapContainer, TileLayer } from 'react-leaflet';
import GeoJsonLayer from './GeoJsonLayer';
import WMSLayer from './WMSLayer';

import Chat from './Chat';
import { ErrorBanner, LoadingOverlay, FeatureInfoPopup, LayerPane, ZoomControl } from './components';
import { useMapLayers } from './hooks';
import type { AppProps } from './types/components';
import type { BasemapOption } from './components/BasemapControl';
import type { LatLng } from 'leaflet';
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
  const [featureInfo, setFeatureInfo] = useState<{
    data: any;
    position: LatLng;
    layerName: string;
  } | null>(null);

  // Basemap configuration
  const basemaps: BasemapOption[] = [
    {
      id: 'none',
      name: 'Brak mapy podkładowej',
      url: '',
      attribution: ''
    },
    {
      id: 'osm',
      name: 'OpenStreetMap',
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    {
      id: 'satellite',
      name: 'Satelitarna (Esri)',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    },
    {
      id: 'topo',
      name: 'Topograficzna (Esri)',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
      attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community'
    },
    {
      id: 'cartodb',
      name: 'CartoDB Positron',
      url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    },
    {
      id: 'dark',
      name: 'Ciemny motyw',
      url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    }
  ];

  const [activeBasemap, setActiveBasemap] = useState('osm');

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
      
      <LayerPane
        layers={layers}
        onToggleLayer={toggleLayer}
        basemaps={basemaps}
        activeBasemap={activeBasemap}
        onBasemapChange={setActiveBasemap}
      />
      
      <div className="map-pane">
        <MapContainer 
          center={[52.23, 18.01]} // Center of Poland
          zoom={6}
          maxZoom={20}
          zoomControl={false}
          style={{ height: '100%', width: '100%' }}
        >
          {activeBasemap !== 'none' && (
            <TileLayer
              key={activeBasemap}
              url={basemaps.find(b => b.id === activeBasemap)?.url || basemaps[1].url}
              attribution={basemaps.find(b => b.id === activeBasemap)?.attribution || basemaps[1].attribution}
              maxZoom={20}
            />
          )}
          
          {layers
            .filter(layer => layer.visible && !layer.loading && !layer.error && layer.type === 'geojson')
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
          
          {layers
            .filter(layer => layer.visible && layer.type === 'wms' && layer.wmsConfig)
            .map((layer) => (
              <WMSLayer
                key={layer.id}
                url={layer.wmsConfig!.url}
                layers={layer.wmsConfig!.layers}
                name={layer.name}
                visible={layer.visible}
                opacity={layer.wmsConfig!.opacity}
                format={layer.wmsConfig!.format}
                transparent={layer.wmsConfig!.transparent}
                maxZoom={layer.wmsConfig!.maxZoom}
                minZoom={layer.wmsConfig!.minZoom}
                onFeatureInfo={(data, latlng) => {
                  setFeatureInfo({
                    data,
                    position: latlng,
                    layerName: layer.name
                  });
                }}
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
          
          <ZoomControl />
          
          {featureInfo && (
            <FeatureInfoPopup
              position={featureInfo.position}
              data={featureInfo.data}
              layerName={featureInfo.layerName}
              onClose={() => setFeatureInfo(null)}
            />
          )}
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