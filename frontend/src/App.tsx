import { useState } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer } from 'react-leaflet';
import GeoJsonLayer from './GeoJsonLayer'; // Import the new component
import 'leaflet/dist/leaflet.css';
import './App.css';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type GeoJsonObject = any;

interface Message {
  sender: 'user' | 'bot';
  text: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [geojson, setGeojson] = useState<GeoJsonObject | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage: Message = { sender: 'user', text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');

    try {
      const response = await axios.post('http://127.0.0.1:8000/api/v1/chat', {
        query: input,
      });

      const { type, data } = response.data;

      if (type === 'geojson') {
        const geojsonData = JSON.parse(data);
        setGeojson(geojsonData); // Set the new data
        const botMessage: Message = { sender: 'bot', text: `Wyświetlono warstwę: ${geojsonData.features[0]?.properties?.loaded_layer || 'dane'}` };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        setGeojson(null); // Clear the map if the response is not geojson
        const botMessage: Message = { sender: 'bot', text: data };
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
          {/* Use the new, robust layer component */}
          {geojson && <GeoJsonLayer data={geojson} />}
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