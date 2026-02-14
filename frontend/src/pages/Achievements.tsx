// frontend/src/pages/Achievements.tsx
// Страница достижений пользователя
// Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface Achievement {
  id: number;
  name: string;
  description: string | null;
  icon_url: string | null;
  condition: any; // не используется в отображении, но присутствует
  earned: boolean;
  earned_at: string | null; // дата получения
}

const Achievements: React.FC = () => {
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAchievements = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get('/api/user/achievements');
        setAchievements(response.data);
      } catch (err) {
        console.error('Failed to fetch achievements:', err);
        setError('Не удалось загрузить достижения. Попробуйте позже.');
      } finally {
        setLoading(false);
      }
    };

    fetchAchievements();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Загрузка достижений...</div>
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
        {/* Заголовок */}
        <div className="mb-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Мои достижения</h1>
          <Link to="/dashboard" className="text-indigo-600 hover:underline">
            ← На главную
          </Link>
        </div>

        {achievements.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500">Пока нет доступных достижений.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {achievements.map((ach) => (
              <div
                key={ach.id}
                className={`bg-white rounded-lg shadow-md overflow-hidden transition ${
                  ach.earned ? 'border-2 border-green-300' : 'opacity-70'
                }`}
              >
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    {ach.icon_url ? (
                      <img
                        src={ach.icon_url}
                        alt={ach.name}
                        className="h-12 w-12 object-contain"
                      />
                    ) : (
                      <div className="h-12 w-12 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 text-2xl">
                        🏆
                      </div>
                    )}
                    {ach.earned && (
                      <span className="px-2 py-1 text-xs font-semibold bg-green-100 text-green-800 rounded-full">
                        Получено
                      </span>
                    )}
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {ach.name}
                  </h3>
                  {ach.description && (
                    <p className="text-sm text-gray-600 mb-3">{ach.description}</p>
                  )}
                  {ach.earned && ach.earned_at && (
                    <p className="text-xs text-gray-400">
                      Получено: {new Date(ach.earned_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Achievements;