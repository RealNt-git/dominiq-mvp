// frontend/src/services/api.ts
// Настроенный axios-клиент для обращения к бэкенду
// Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

import axios from 'axios';

// Базовый URL из переменной окружения или значение по умолчанию
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для добавления email пользователя в каждый запрос
api.interceptors.request.use((config) => {
  const email = localStorage.getItem('userEmail');
  if (email) {
    config.headers['X-User-Email'] = email;
  }
  return config;
});

export default api;