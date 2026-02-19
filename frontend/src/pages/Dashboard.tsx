// frontend/src/pages/Dashboard.tsx
// Дашборд студента: приветствие, прогресс, ссылки на разделы
// Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0
// Добавлены ссылки на соответствующие страницы для блоков статистики (карточки, квизы, достижения)

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface ProgressData {
  total_xp: number;
  level: number;
  cards_studied: number;
  quizzes_passed: number;
  achievements_count: number;
}

const Dashboard: React.FC = () => {
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const userEmail = localStorage.getItem('userEmail') || 'Пользователь';

  useEffect(() => {
    const fetchProgress = async () => {
      try {
        const response = await api.get('/api/user/progress');
        setProgress(response.data);
      } catch (err) {
        console.error('Failed to fetch progress:', err);
        setError('Не удалось загрузить данные прогресса');
      } finally {
        setLoading(false);
      }
    };

    fetchProgress();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Загрузка...</div>
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
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Приветствие */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Привет, {userEmail}!
          </h1>
          <p className="mt-2 text-gray-600">
            Продолжай учиться. Твой текущий уровень — {progress?.level}
          </p>
        </div>

        {/* Статистика со ссылками */}
        {progress && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
            {/* Блок XP без ссылки (нет отдельной страницы) */}
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Всего опыта (XP)
                </dt>
                <dd className="mt-1 text-3xl font-semibold text-gray-900">
                  {progress.total_xp}
                </dd>
              </div>
            </div>

            {/* Карточки – ссылка на /cards */}
            <Link to="/cards" className="block group">
              <div className="bg-white overflow-hidden shadow rounded-lg transition group-hover:shadow-lg">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Изучено карточек
                  </dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900">
                    {progress.cards_studied}
                  </dd>
                </div>
              </div>
            </Link>

            {/* Квизы – ссылка на /quizzes */}
            <Link to="/quizzes" className="block group">
              <div className="bg-white overflow-hidden shadow rounded-lg transition group-hover:shadow-lg">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Пройдено квизов
                  </dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900">
                    {progress.quizzes_passed}
                  </dd>
                </div>
              </div>
            </Link>

            {/* Достижения – ссылка на /achievements */}
            <Link to="/achievements" className="block group">
              <div className="bg-white overflow-hidden shadow rounded-lg transition group-hover:shadow-lg">
                <div className="px-4 py-5 sm:p-6">
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Достижений
                  </dt>
                  <dd className="mt-1 text-3xl font-semibold text-gray-900">
                    {progress.achievements_count}
                  </dd>
                </div>
              </div>
            </Link>
          </div>
        )}

        {/* Разделы обучения */}
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Продолжить обучение</h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <Link
            to="/cards"
            className="block p-6 bg-white rounded-lg border border-gray-200 shadow-md hover:bg-indigo-50 transition"
          >
            <h5 className="mb-2 text-2xl font-bold tracking-tight text-gray-900">
              Карточки
            </h5>
            <p className="font-normal text-gray-700">
              Повторяй термины с помощью интервальных повторений.
            </p>
          </Link>
          <Link
            to="/quizzes"
            className="block p-6 bg-white rounded-lg border border-gray-200 shadow-md hover:bg-indigo-50 transition"
          >
            <h5 className="mb-2 text-2xl font-bold tracking-tight text-gray-900">
              Квизы
            </h5>
            <p className="font-normal text-gray-700">
              Проверяй свои знания с помощью тестов.
            </p>
          </Link>
          <Link
            to="/achievements"
            className="block p-6 bg-white rounded-lg border border-gray-200 shadow-md hover:bg-indigo-50 transition"
          >
            <h5 className="mb-2 text-2xl font-bold tracking-tight text-gray-900">
              Достижения
            </h5>
            <p className="font-normal text-gray-700">
              Смотри свои награды и прогресс.
            </p>
          </Link>
        </div>

        {/* Рекомендуемые темы (опционально) */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Рекомендуемые темы</h2>
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              <li className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-indigo-600 truncate">
                    Основы ритейла
                  </p>
                  <div className="ml-2 flex-shrink-0">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                      5 карточек
                    </span>
                  </div>
                </div>
              </li>
              <li className="px-4 py-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-indigo-600 truncate">
                    Управление запасами
                  </p>
                  <div className="ml-2 flex-shrink-0">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                      8 карточек
                    </span>
                  </div>
                </div>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;