import React, { useState, useEffect, useCallback } from 'react';

/**
 * Toast notification component.
 * Usage: <Toast messages={messages} onDismiss={dismissToast} />
 */
export function ToastContainer({ messages, onDismiss }) {
  return (
    <div className="toast-container">
      {messages.map(msg => (
        <ToastItem key={msg.id} message={msg} onDismiss={onDismiss} />
      ))}
    </div>
  );
}

function ToastItem({ message, onDismiss }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(message.id), 3500);
    return () => clearTimeout(timer);
  }, [message.id, onDismiss]);

  const typeClass = message.type === 'error' ? 'toast--error'
    : message.type === 'success' ? 'toast--success'
    : 'toast--info';

  return (
    <div className={`toast-item ${typeClass}`}>
      <span>{message.text}</span>
      <button className="toast-close" onClick={() => onDismiss(message.id)}>✕</button>
    </div>
  );
}

/** Custom hook to manage toast messages */
export function useToast() {
  const [messages, setMessages] = useState([]);

  const addToast = useCallback((text, type = 'info') => {
    const id = Date.now() + Math.random();
    setMessages(prev => [...prev, { id, text, type }]);
  }, []);

  const dismissToast = useCallback((id) => {
    setMessages(prev => prev.filter(m => m.id !== id));
  }, []);

  return { messages, addToast, dismissToast };
}
