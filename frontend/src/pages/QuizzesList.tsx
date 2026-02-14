// frontend/src/pages/QuizzesList.tsx
// Страница со списком доступных квизов
// Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface Quiz {
  id: number;
  title: string;
  topic_id: number;
  // В будущем можно добавить количество вопросов, если API будет отдавать
}

const QuizzesList: React.FC = () => {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchQuizzes = async () => {
      setLoading(true);
      try {
        const response = await api.get('/api/quizzes');
        setQuizzes(response.data);
      } catch (err) {
        console.error('Failed to fetch quizzes:', err);
        setError('Не удалось загрузить список квизов');
      } finally {
        setLoading(false);
      }
    };

    fetchQuizzes();
  }, []);

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
        <div className="mb-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Доступные квизы</h1>
          <Link
            to="/dashboard"
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            На главную
          </Link>
        </div>

        {quizzes.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">Пока нет доступных квизов.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {quizzes.map((quiz) => (
              <div
                key={quiz.id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition"
              >
                <div className="p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {quiz.title}
                  </h3>
                  <p className="text-sm text-gray-500 mb-4">
                    Тема ID: {quiz.topic_id}
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