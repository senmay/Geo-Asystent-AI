/**
 * Chat message component for displaying individual messages
 */

import React from 'react';
import type { ChatMessageProps } from '../types/components';

const ChatMessage: React.FC<ChatMessageProps> = ({ message, className = '' }) => {
  const getMessageTypeClass = () => {
    if (message.type === 'info') return 'chat-message-info';
    if (message.type === 'data') return 'chat-message-data';
    return '';
  };

  return (
    <div 
      className={`chat-message ${message.sender} ${getMessageTypeClass()} ${className}`}
      style={{
        padding: '8px 12px',
        margin: '4px 0',
        borderRadius: '8px',
        maxWidth: '80%',
        wordWrap: 'break-word',
        ...(message.sender === 'user' ? {
          backgroundColor: '#007bff',
          color: 'white',
          marginLeft: 'auto',
          textAlign: 'right'
        } : {
          backgroundColor: '#f1f1f1',
          color: '#333',
          marginRight: 'auto'
        }),
        ...(message.type === 'info' ? {
          fontStyle: 'italic',
          opacity: 0.8,
          fontSize: '0.9em'
        } : {}),
        ...(message.type === 'data' ? {
          fontWeight: '500'
        } : {})
      }}
    >
      {message.text}
    </div>
  );
};

export default ChatMessage;