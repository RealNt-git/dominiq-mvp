// frontend/src/pages/admin/DocumentUpload.tsx
// Страница загрузки документа для AI-обработки (методолог)
// Добавлен выбор темы из списка тем домена или создание новой темы
// Учтена тема "Общая" по умолчанию

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';

// Предопределённые домены (можно расширить позже)
const AVAILABLE_DOMAINS = ['Ритейл', 'Финтех'];

interface Topic {
  id: number;
  name: string;
  domain_id: number;
}

const DocumentUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [domain, setDomain] = useState<string>(AVAILABLE_DOMAINS[0]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [selectedTopicId, setSelectedTopicId] = useState<number | ''>('');
  const [isCreatingNewTopic, setIsCreatingNewTopic] = useState(false);
  const [newTopicName, setNewTopicName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const navigate = useNavigate();

  // Загрузка тем при изменении домена
  useEffect(() => {
    const fetchTopics = async () => {
      try {
        // Сначала получаем ID домена по имени
        const domainsRes = await api.get('/api/domains');
        const domainObj = domainsRes.data.find((d: any) => d.name === domain);
        if (domainObj) {
          const topicsRes = await api.get(`/api/topics?domain_id=${domainObj.id}`);
          setTopics(topicsRes.data);
        } else {
          setTopics([]);
        }
      } catch (err) {
        console.error('Failed to fetch topics:', err);
        setError('Не удалось загрузить список тем');
      }
    };
    fetchTopics();
  }, [domain]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDomainChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setDomain(e.target.value);
    setSelectedTopicId('');
    setIsCreatingNewTopic(false);
    setNewTopicName('');
  };

  const handleTopicChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (value === 'new') {
      setIsCreatingNewTopic(true);
      setSelectedTopicId('');
    } else {
      setIsCreatingNewTopic(false);
      setSelectedTopicId(value ? Number(value) : '');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Выберите файл для загрузки');
      return;
    }

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext !== 'txt' && ext !== 'md') {
      setError('Допустимы только файлы .txt и .md');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccessMessage(null);

    try {
      // Если создаётся новая тема, сначала создаём её
      let topicIdToUse = selectedTopicId;
      if (isCreatingNewTopic) {
        if (!newTopicName.trim()) {
          setError('Введите название новой темы');
          setUploading(false);
          return;
        }
        // Получаем ID домена
        const domainsRes = await api.get('/api/domains');
        const domainObj = domainsRes.data.find((d: any) => d.name === domain);
        if (!domainObj) {
          throw new Error('Домен не найден');
        }
        const createRes = await api.post('/api/topics', {
          name: newTopicName,
          domain_id: domainObj.id,
        });
        topicIdToUse = createRes.data.id;
      }

      // Загружаем документ
      const formData = new FormData();
      formData.append('file', file);
      formData.append('domain', domain);
      if (topicIdToUse) {
        formData.append('topic_id', String(topicIdToUse));
      }

      const response = await api.post('/api/admin/ai/upload-document', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const { document_id } = response.data;
      setSuccessMessage(`Документ успешно загружен. ID: ${document_id}`);
      setTimeout(() => navigate('/admin/drafts'), 2000);
    } catch (err: any) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Ошибка при загрузке документа');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Загрузка документа</h1>

        <form onSubmit={handleSubmit} className="bg-white shadow-lg rounded-lg p-6">
          {/* Выбор файла */}
          <div className="mb-6">
            <label htmlFor="file" className="block text-sm font-medium text-gray-700 mb-2">
              Файл (.txt или .md)
            </label>
            <input
              type="file"
              id="file"
              accept=".txt,.md"
              onChange={handleFileChange}
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
            />
          </div>

          {/* Выбор домена */}
          <div className="mb-6">
            <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-2">
              Предметная область
            </label>
            <select
              id="domain"
              value={domain}
              onChange={handleDomainChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              {AVAILABLE_DOMAINS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          {/* Выбор темы */}
          <div className="mb-6">
            <label htmlFor="topic" className="block text-sm font-medium text-gray-700 mb-2">
              Тема документа
            </label>
            <select
              id="topic"
              value={isCreatingNewTopic ? 'new' : selectedTopicId}
              onChange={handleTopicChange}
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="">-- Выберите тему --</option>
              {topics.map((topic) => (
                <option key={topic.id} value={topic.id}>{topic.name}</option>
              ))}
              <option value="new">➕ Создать новую тему...</option>
            </select>
          </div>

          {/* Поле для новой темы */}
          {isCreatingNewTopic && (
            <div className="mb-6">
              <label htmlFor="newTopic" className="block text-sm font-medium text-gray-700 mb-2">
                Название новой темы
              </label>
              <input
                type="text"
                id="newTopic"
                value={newTopicName}
                onChange={(e) => setNewTopicName(e.target.value)}
                placeholder="Например: Управление запасами"
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              />
            </div>
          )}

          {/* Сообщения об ошибке/успехе */}
          {error && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md text-sm">{error}</div>
          )}
          {successMessage && (
            <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-md text-sm">
              {successMessage} Перенаправление...
            </div>
          )}

          {/* Кнопка отправки */}
          <button
            type="submit"
            disabled={uploading || !file}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300 disabled:cursor-not-allowed"
          >
            {uploading ? 'Загрузка и обработка...' : 'Загрузить и обработать'}
          </button>
        </form>

        {/* Кнопка назад */}
        <div className="mt-4 text-center">
          <button
            onClick={() => navigate('/admin/drafts')}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Перейти к черновикам
          </button>
        </div>
      </div>
    </div>
  );
};

export default DocumentUpload;