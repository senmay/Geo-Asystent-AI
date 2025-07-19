/**
 * Chat input component for message input and submission
 */

import React from 'react';
import type { ChatInputProps } from '../types/components';

const ChatInput: React.FC<ChatInputProps> = ({ 
  value, 
  onChange, 
  onSubmit, 
  disabled = false, 
  placeholder = 'Wpisz wiadomość...' 
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim() || disabled) return;
    onSubmit();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form 
      onSubmit={handleSubmit} 
      className="chat-input-form"
      style={{
        display: 'flex',
        padding: '16px',
        borderTop: '1px solid #e0e0e0',
        backgroundColor: '#fff',
        gap: '8px'
      }}
    >
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyPress={handleKeyPress}
        placeholder={placeholder}
        disabled={disabled}
        style={{
          flex: 1,
          padding: '12px 16px',
          border: '1px solid #ddd',
          borderRadius: '24px',
          fontSize: '14px',
          outline: 'none',
          backgroundColor: disabled ? '#f5f5f5' : '#fff',
          color: disabled ? '#999' : '#333'
        }}
      />
      <button 
        type="submit" 
        disabled={disabled || !value.trim()}
        style={{
          padding: '12px 24px',
          backgroundColor: disabled || !value.trim() ? '#ccc' : '#007bff',
          color: 'white',
          border: 'none',
          borderRadius: '24px',
          fontSize: '14px',
          fontWeight: '500',
          cursor: disabled || !value.trim() ? 'not-allowed' : 'pointer',
          transition: 'background-color 0.2s'
        }}
      >
        {disabled ? 'Wysyłam...' : 'Wyślij'}
      </button>
    </form>
  );
};

export default ChatInput;