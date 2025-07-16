

import { useState, useEffect } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer } from 'react-leaflet';
import GeoJsonLayer from './GeoJsonLayer';
import LayerControl, { type LayerState } from './LayerControl';
import 'leaflet/dist/leaflet.css';
import './App.css';

interface Message {
  sender: 'user' | 'bot';
  text: string;
  type?: 'info' | 'data';
}

const intentToFriendlyName: { [key: string]: string } = {
  get_gis_data: 'Pobieranie warstwy GIS',
  find_largest_parcel: 'Wyszukiwanie największej działki',
  find_n_largest_parcels: 'Wyszukiwanie N największych działek',
  find_parcels_above_area: 'Wyszukiwanie działek powyżej określonej powierzchni',
  find_parcels_near_gpz: 'Wyszukiwanie działek w pobliżu GPZ',
  chat: 'Rozmowa ogólna',
};

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [layers, setLayers] = useState<LayerState[]>([]); // For base layers
  const [queryGeojson, setQueryGeojson] = useState<any>(null); // For query results

  // Fetch initial layers on component mount
  useEffect(() => {
    const fetchInitialLayers = async () => {
      try {
        const initialLayerNames = [
          { name: 'GPZ 110kV', apiName: 'gpz_110kv' },
          { name: 'Budynki', apiName: 'buildings' },
          { name: 'Działki', apiName: 'parcels' },
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
        }));

        setLayers(initialLayers);

      } catch (error) {
        console.error('Error fetching initial layers:', error);
        const errorMessage: Message = {
          sender: 'bot',
          text: 'Nie udało się załadować warstw początkowych.',
        };
        setMessages(prev => [...prev, errorMessage]);
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setQueryGeojson(null); // Clear previous query results

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/v1/chat', {
        query: currentInput,
      });

      const { type, data, intent } = response.data;

      if (intent && intentToFriendlyName[intent]) {
        const infoMessage: Message = {
          sender: 'bot',
          text: `Używam narzędzia: "${intentToFriendlyName[intent]}"`, 
          type: 'info',
        };
        setMessages((prev) => [...prev, infoMessage]);
      }

      if (type === 'geojson') {
        const geojsonData = JSON.parse(data);
        setQueryGeojson(geojsonData); // Set query result

        const messagesFromFeatures = geojsonData.features
          ?.map((feature: any) => feature.properties?.message)
          .filter(Boolean);

        let botMessageText;
        if (messagesFromFeatures?.length > 0) {
          botMessageText = messagesFromFeatures.join('\n');
        } else {
          botMessageText = `Wyświetlono ${geojsonData.features?.length || 0} obiektów na mapie.`;
        }

        const botMessage: Message = { sender: 'bot', text: botMessageText, type: 'data' };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        const botMessage: Message = { sender: 'bot', text: data, type: 'data' };
        setMessages((prev) => [...prev, botMessage]);
      }
    } catch (error) {
      console.error('Error communicating with backend:', error);
      const errorMessage: Message = {
        sender: 'bot',
        text: 'Wystąpił błąd podczas komunikacji z serwerem.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
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
            layer.visible && <GeoJsonLayer key={layer.id} data={layer.data} />
          )}
          {queryGeojson && <GeoJsonLayer data={queryGeojson} color="#FF0000" />} {/* Highlight query results in red */}
          <LayerControl layers={layers} onToggleLayer={handleToggleLayer} />
        </MapContainer>
      </div>
      <div className="chat-pane">
        <div className="chat-history">
          {messages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.sender}`}>
              {msg.text}
            </div>
          ))}
        </div>
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Zapytaj o dane GIS..."
          />
          <button type="submit">Wyślij</button>
        </form>
      </div>
    </div>
  );
}

export default App;
