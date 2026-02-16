// frontend/src/pages/QuizzesList.tsx
// Страница со списком доступных квизов с фильтрацией по домену, теме и названию

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface Domain {
  id: number;
  name: string;
}

interface Topic {
  id: number;
  name: string;
  domain_id: number;
}

interface Quiz {
  id: number;
  title: string;
  topic_id: number;
  topic_name: string;
  domain_name: string;
}

const QuizzesList: React.FC = () => {
  const [domains, setDomains] = useState<Domain[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [filteredQuizzes, setFilteredQuizzes] = useState<Quiz[]>([]);
  
  const [selectedDomainId, setSelectedDomainId] = useState<number | ''>('');
  const [selectedTopicId, setSelectedTopicId] = useState<number | ''>('');
  const [searchTerm, setSearchTerm] = useState('');

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [domainsRes, topicsRes, quizzesRes] = await Promise.all([
          api.get('/api/domains'),
          api.get('/api/topics'),
          api.get('/api/quizzes'),
        ]);
        setDomains(domainsRes.data);
        setTopics(topicsRes.data);
        setQuizzes(quizzesRes.data);
        setFilteredQuizzes(quizzesRes.data);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setError('Не удалось загрузить данные');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  // Применяем фильтры при изменении параметров
  useEffect(() => {
    let filtered = quizzes;

    // Фильтр по домену
    if (selectedDomainId !== '') {
      const domainId = Number(selectedDomainId);
      // Сначала находим все темы этого домена
      const topicIdsForDomain = topics
        .filter(t => t.domain_id === domainId)
        .map(t => t.id);
      filtered = filtered.filter(q => topicIdsForDomain.includes(q.topic_id));
    }

    // Фильтр по теме
    if (selectedTopicId !== '') {
      const topicId = Number(selectedTopicId);
      filtered = filtered.filter(q => q.topic_id === topicId);
    }

    // Поиск по названию
    if (searchTerm.trim() !== '') {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(q => q.title.toLowerCase().includes(term));
    }

    setFilteredQuizzes(filtered);
  }, [selectedDomainId, selectedTopicId, searchTerm, quizzes, topics]);

  // Получаем темы, принадлежащие выбранному домену (для выпадающего списка)
  const topicsForSelectedDomain = selectedDomainId
    ? topics.filter(t => t.domain_id === selectedDomainId)
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Загрузка квизов...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-500 text-lg">{error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-3xl font-bold text-gray-900">Доступные квизы</h1>
          <Link
            to="/dashboard"
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            На главную
          </Link>
        </div>

        {/* Фильтры */}
        <div className="mb-6 bg-white p-4 rounded shadow flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <label htmlFor="domainFilter" className="block text-sm font-medium text-gray-700 mb-1">
              Домен
            </label>
            <select
              id="domainFilter"
              value={selectedDomainId}
              onChange={(e) => {
                setSelectedDomainId(e.target.value ? Number(e.target.value) : '');
                setSelectedTopicId(''); // сбрасываем тему при смене домена
              }}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="">Все домены</option>
              {domains.map(domain => (
                <option key={domain.id} value={domain.id}>{domain.name}</option>
              ))}
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label htmlFor="topicFilter" className="block text-sm font-medium text-gray-700 mb-1">
              Тема
            </label>
            <select
              id="topicFilter"
              value={selectedTopicId}
              onChange={(e) => setSelectedTopicId(e.target.value ? Number(e.target.value) : '')}
              disabled={!selectedDomainId}
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md disabled:bg-gray-100 disabled:text-gray-500"
            >
              <option value="">Все темы</option>
              {topicsForSelectedDomain.map(topic => (
                <option key={topic.id} value={topic.id}>{topic.name}</option>
              ))}
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-1">
              Поиск по названию
            </label>
            <input
              type="text"
              id="search"
              placeholder="Введите название квиза"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
            />
          </div>
        </div>

        {/* Список квизов */}
        {filteredQuizzes.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">Нет квизов, соответствующих выбранным фильтрам.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredQuizzes.map((quiz) => (
              <div
                key={quiz.id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition"
              >
                <div className="p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {quiz.title}
                  </h3>
                  <p className="text-sm text-gray-500 mb-2">
                    Тема: <span className="font-medium text-gray-700">{quiz.topic_name}</span>
                  </p>
                  <p className="text-sm text-gray-500 mb-4">
                    Домен: <span className="font-medium text-gray-700">{quiz.domain_name}</span>
                  </p>
                  <Link
                    to={`/quiz/${quiz.id}`}
                    className="inline-block px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                  >
                    Пройти квиз
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default QuizzesList;