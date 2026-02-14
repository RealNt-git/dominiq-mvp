// frontend/src/main.tsx
// Точка входа React

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css'; // если есть глобальные стили

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);