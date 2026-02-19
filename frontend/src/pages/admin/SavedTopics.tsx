// frontend/src/pages/admin/SavedTopics.tsx
import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../../services/api';

interface Session {
  id: number;
  domain: string;
  role: string;
  step: string;
  suggested_topics: { name: string; description: string }[] | null;
  selected_topics: string[] | null;
  generated_content: { name: string; content: string }[] | null;
  created_at: string;
  updated_at: string;
}

const SavedTopics: React.FC = () => {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/admin/ai/topics/sessions');
      setSessions(response.data);
    } catch (err: any) {
      console.error('Failed to fetch sessions:', err);
      setError('Не удалось загрузить сохранённые сессии');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Удалить эту сессию?')) return;
    try {
      await api.delete(`/api/admin/ai/topics/sessions/${id}`);
      fetchSessions();
    } catch (err) {
      console.error('Failed to delete session:', err);
      setError('Ошибка при удалении');
    }
  };

  const handleContinue = (session: Session) => {
    // Передаём состояние сессии через location.state
    navigate('/admin/topics', { state: { session } });
  };

  const getStepName = (step: string) => {
    const steps: Record<string, string> = {
      input: 'Ввод домена',
      suggestions: 'Выбор тем',
      content: 'Генерация контента',
      done: 'Завершено',
    };
    return steps[step] || step;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Загрузка...</div>
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

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Сохранённые сессии подбора тем</h1>
          <Link to="/admin/topics" className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
            Новая сессия
          </Link>
        </div>

        {sessions.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-6 text-center">
            <p className="text-gray-500">У вас нет сохранённых сессий.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {sessions.map((session) => (
              <div key={session.id} className="bg-white shadow rounded-lg overflow-hidden">
                <div className="p-6">
                  <h3 className="text-xl font-semibold mb-2">{session.domain}</h3>
                  <p className="text-sm text-gray-600 mb-1">Роль: {session.role}</p>
                  <p className="text-sm text-gray-600 mb-2">Этап: {getStepName(session.step)}</p>
                  <p className="text-xs text-gray-400">
                    Последнее изменение: {new Date(session.updated_at).toLocaleString()}
                  </p>
                  <div className="mt-4 flex justify-end gap-2">
                    <button
                      onClick={() => handleContinue(session)}
                      className="px-3 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700"
                    >
                      Продолжить
                    </button>
                    <button
                      onClick={() => handleDelete(session.id)}
                      className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                    >
                      Удалить
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default SavedTopics;