
import React, { useState } from 'react';
import { useChat } from './hooks';
import { ErrorBanner, ChatHistory, ChatInput } from './components';
import type { ChatProps } from './types/components';

const Chat: React.FC<ChatProps> = ({ setQueryGeojson }) => {
  const [input, setInput] = useState('');
  const { messages, sendMessage, isLoading, error, clearError } = useChat(setQueryGeojson);

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    const currentInput = input;
    setInput('');
    clearError();

    await sendMessage(currentInput);
  };

  return (
    <div 
      className="chat-pane"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        backgroundColor: '#fff',
        borderLeft: '1px solid #e0e0e0'
      }}
    >
      <div 
        className="chat-header"
        style={{
          padding: '16px',
          borderBottom: '1px solid #e0e0e0',
          backgroundColor: '#f8f9fa'
        }}
      >
        <h3 style={{ margin: 0, fontSize: '16px', fontWeight: '600' }}>
          Asystent GIS
        </h3>
        <p style={{ margin: '4px 0 0 0', fontSize: '12px', color: '#666' }}>
          Zadaj pytanie o dane przestrzenne
        </p>
      </div>

      <ErrorBanner 
        error={error} 
        onDismiss={clearError}
        type="error"
      />
      
      <ChatHistory 
        messages={messages}
        isLoading={isLoading}
        loadingMessage="Przetwarzam zapytanie..."
      />
      
      <ChatInput
        value={input}
        onChange={setInput}
        onSubmit={handleSubmit}
        disabled={isLoading}
        placeholder="Zapytaj o dane GIS..."
      />
    </div>
  );
};

export default Chat;
