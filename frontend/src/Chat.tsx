
import React, { useState } from 'react';
import axios from 'axios';

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

interface ChatProps {
  setQueryGeojson: (geojson: any) => void;
}

const Chat: React.FC<ChatProps> = ({ setQueryGeojson }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

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
  );
};

export default Chat;
