/**
 * Chat history component for displaying message list
 */

import React from 'react';
import ChatMessage from './ChatMessage';
import type { ChatHistoryProps } from '../types/components';

const ChatHistory: React.FC<ChatHistoryProps> = ({ 
  messages, 
  isLoading = false, 
  loadingMessage = 'Przetwarzam zapytanie...' 
}) => {
  return (
    <div 
      className="chat-history"
      style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
      }}
    >
      {messages.map((message, index) => (
        <ChatMessage key={index} message={message} />
      ))}
      
      {isLoading && (
        <div 
          className="chat-message bot loading"
          style={{
            backgroundColor: '#f1f1f1',
            color: '#666',
            padding: '8px 12px',
            borderRadius: '8px',
            maxWidth: '80%',
            fontStyle: 'italic',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <div 
            className="loading-dots"
            style={{
              display: 'inline-block',
              width: '20px',
              height: '20px'
            }}
          >
            <div style={{
              display: 'inline-block',
              width: '4px',
              height: '4px',
              borderRadius: '50%',
              backgroundColor: '#666',
              animation: 'loading-dots 1.4s infinite ease-in-out both',
              marginRight: '2px'
            }} />
            <div style={{
              display: 'inline-block',
              width: '4px',
              height: '4px',
              borderRadius: '50%',
              backgroundColor: '#666',
              animation: 'loading-dots 1.4s infinite ease-in-out both',
              animationDelay: '0.16s',
              marginRight: '2px'
            }} />
            <div style={{
              display: 'inline-block',
              width: '4px',
              height: '4px',
              borderRadius: '50%',
              backgroundColor: '#666',
              animation: 'loading-dots 1.4s infinite ease-in-out both',
              animationDelay: '0.32s'
            }} />
          </div>
          {loadingMessage}
        </div>
      )}
      
      <style>{`
        @keyframes loading-dots {
          0%, 80%, 100% {
            transform: scale(0);
          }
          40% {
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
};

export default ChatHistory;