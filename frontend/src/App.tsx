import { useState, useEffect } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer } from 'react-leaflet';
import GeoJsonLayer from './GeoJsonLayer';
import LayerControl, { type LayerState } from './LayerControl';
import Chat from './Chat'; // Import the new Chat component
import 'leaflet/dist/leaflet.css';
import './App.css';

function App() {
  const [layers, setLayers] = useState<LayerState[]>([]); // For base layers
  const [queryGeojson, setQueryGeojson] = useState<any>(null); // For query results

  // Fetch initial layers on component mount
  useEffect(() => {
    const fetchInitialLayers = async () => {
      try {
        const initialLayerNames = [
          { name: 'GPZ 110kV', apiName: 'gpz_110kv', color: '#ff0000' }, // Red for GPZ
          { name: 'Budynki', apiName: 'buildings', color: '#3388ff' }, // Leaflet blue for Buildings
          { name: 'Działki', apiName: 'parcels', color: '#00ff00' }, // Green for Parcels
        ];

        const layerPromises = initialLayerNames.map(layerInfo =>
          axios.get(`http://127.0.0.1:8000/api/v1/layers/${layerInfo.apiName}`)
        );

        const responses = await Promise.all(layerPromises);

        const initialLayers: LayerState[] = responses.map((response, index) => ({
          id: Date.now() + index,
          name: initialLayerNames[index].name,
          data: response.data,
          visible: true,
          color: initialLayerNames[index].color, // Pass the color to LayerState
        }));

        setLayers(initialLayers);

      } catch (error) {
        console.error('Error fetching initial layers:', error);
        // You might want to set an error message in a state to display to the user
      }
    };

    fetchInitialLayers();
  }, []);

  const handleToggleLayer = (id: number) => {
    setLayers((prevLayers) =>
      prevLayers.map((layer) =>
        layer.id === id ? { ...layer, visible: !layer.visible } : layer
      )
    );
  };

  return (
    <div className="app-container">
      <div className="map-pane">
        <MapContainer center={[52.237049, 21.017532]} zoom={13} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          />
          {layers.map((layer) =>
            layer.visible && <GeoJsonLayer key={layer.id} data={layer.data} layerName={layer.name} />
          )}
          {queryGeojson && <GeoJsonLayer data={queryGeojson} color="#FF0000" />} {/* Highlight query results in red */}
          <LayerControl layers={layers} onToggleLayer={handleToggleLayer} />
        </MapContainer>
      </div>
      <Chat setQueryGeojson={setQueryGeojson} />
    </div>
  );
}

export default App;