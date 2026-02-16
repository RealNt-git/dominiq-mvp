// frontend/src/pages/MyPlan.tsx
// Страница личного кабинета пользователя – отображение плана развития и прогресса
// Добавлена подсказка о способах повышения прогресса

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';

interface Topic {
  id: number;
  name: string;
}

interface Grade {
  id: number;
  name: string;
}

interface Plan {
  id: number;
  topic_id: number;
  grade_id: number;
  priority: number;
  target_date: string | null;
  status: string;
  total_terms: number;
  studied_terms: number;
  topic: Topic;
  grade: Grade;
}

const MyPlan: React.FC = () => {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlans = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await api.get('/api/plan/plans/my');
        setPlans(response.data);
      } catch (err) {
        console.error('Failed to load my plan:', err);
        setError('Не удалось загрузить ваш план развития');
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Загрузка вашего плана...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-500 text-lg">{error}</div>
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Мой план развития</h1>
          <p className="text-gray-600 mb-8">У вас пока нет назначенных планов.</p>
          <Link to="/dashboard" className="text-indigo-600 hover:underline">
            Вернуться на главную
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Мой план развития</h1>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {plans.map((plan) => {
            const percent = plan.total_terms > 0
              ? Math.round((plan.studied_terms / plan.total_terms) * 100)
              : 0;
            const remaining = plan.total_terms - plan.studied_terms;
            return (
              <div
                key={plan.id}
                className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition"
              >
                <div className="p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    {plan.topic.name}
                  </h3>
                  <div className="space-y-2 text-sm text-gray-600">
                    <p>🎯 Целевой грейд: <span className="font-medium">{plan.grade.name}</span></p>
                    <p>📊 Приоритет: <span className="font-medium">{plan.priority}</span></p>
                    {plan.target_date && (
                      <p>📅 Срок: <span className="font-medium">{new Date(plan.target_date).toLocaleDateString('ru-RU')}</span></p>
                    )}
                    <p>📚 Прогресс: {plan.studied_terms} из {plan.total_terms} терминов</p>
                    {remaining > 0 && (
                      <p className="text-xs text-gray-400">Осталось изучить: {remaining} терминов</p>
                    )}
                  </div>
                  <div className="mt-4">
                    <div className="w-full bg-gray-200 rounded-full h-2.5">
                      <div
                        className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                        style={{ width: `${percent}%` }}
                      ></div>
                    </div>
                    <p className="text-right text-sm text-gray-500 mt-1">{percent}%</p>
                  </div>
                  {/* Подсказка */}
                  <div className="mt-4 text-xs text-gray-500 bg-gray-50 p-2 rounded">
                    💡 Чтобы повысить прогресс, изучайте карточки и проходите квизы по этой теме.
                  </div>
                  <div className="mt-4">
                    <Link
                      to={`/cards?topic_id=${plan.topic_id}`}
                      className="inline-block w-full text-center px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 transition"
                    >
                      Изучать тему
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default MyPlan;