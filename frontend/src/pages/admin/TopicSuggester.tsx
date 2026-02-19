// frontend/src/pages/admin/TopicSuggester.tsx (полный обновлённый файл)
import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import api from '../../services/api';

// Компонент спиннера
const Loader: React.FC = () => (
  <div className="flex justify-center items-center py-4">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
  </div>
);

interface SuggestedTopic {
  name: string;
  description: string;
}

interface TopicWithContent {
  name: string;
  content: string;
}

interface Session {
  id: number;
  domain: string;
  role: string;
  step: string;
  suggested_topics: SuggestedTopic[] | null;
  selected_topics: string[] | null;
  generated_content: TopicWithContent[] | null;
}

const TopicSuggester: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const sessionFromState = location.state?.session as Session | undefined;

  const [domain, setDomain] = useState(sessionFromState?.domain || '');
  const [role, setRole] = useState(sessionFromState?.role || 'аналитик');
  const [suggestedTopics, setSuggestedTopics] = useState<SuggestedTopic[]>(
    sessionFromState?.suggested_topics || []
  );
  const [selectedTopics, setSelectedTopics] = useState<string[]>(
    sessionFromState?.selected_topics || []
  );
  const [generatedContent, setGeneratedContent] = useState<TopicWithContent[]>(
    sessionFromState?.generated_content || []
  );
  const [step, setStep] = useState<'input' | 'suggestions' | 'content' | 'done'>(
    sessionFromState?.step as any || 'input'
  );
  const [sessionId, setSessionId] = useState<number | null>(sessionFromState?.id || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [customTopicName, setCustomTopicName] = useState('');
  const [isAddingCustom, setIsAddingCustom] = useState(false);

  const saveSession = async () => {
    if (!domain) return;
    const sessionData = {
      domain,
      role,
      step,
      suggested_topics: suggestedTopics,
      selected_topics: selectedTopics,
      generated_content: generatedContent,
    };
    try {
      if (sessionId) {
        await api.put(`/api/admin/ai/topics/sessions/${sessionId}`, sessionData);
      } else {
        const response = await api.post('/api/admin/ai/topics/sessions', sessionData);
        setSessionId(response.data.id);
      }
      setSavedMessage('Сохранено');
      setTimeout(() => setSavedMessage(null), 2000);
    } catch (err) {
      console.error('Failed to save session:', err);
      setError('Ошибка сохранения');
    }
  };

  const handleSuggest = async () => {
    if (!domain.trim()) {
      setError('Введите домен');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/api/admin/ai/topics/suggest', { domain, role });
      setSuggestedTopics(response.data.topics);
      setSelectedTopics(response.data.topics.map((t: SuggestedTopic) => t.name));
      setStep('suggestions');
      await saveSession();
    } catch (err: any) {
      console.error('Failed to suggest topics:', err);
      setError(err.response?.data?.detail || 'Ошибка при подборе тем');
    } finally {
      setLoading(false);
    }
  };

  const handleRegenerateTopic = async (index: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/api/admin/ai/topics/suggest', { domain, role });
      const newTopics = response.data.topics;
      const updated = [...suggestedTopics];
      updated[index] = newTopics[index % newTopics.length];
      setSuggestedTopics(updated);
      setSelectedTopics(updated.map(t => t.name));
      await saveSession();
    } catch (err: any) {
      console.error('Failed to regenerate topic:', err);
      setError('Ошибка при замене темы');
    } finally {
      setLoading(false);
    }
  };

  const handleTopicNameChange = (index: number, newName: string) => {
    const updated = [...suggestedTopics];
    updated[index] = { ...updated[index], name: newName };
    setSuggestedTopics(updated);
    setSelectedTopics(updated.map(t => t.name));
  };

  const handleDeleteTopic = (index: number) => {
    if (!window.confirm('Удалить эту тему?')) return;
    const updated = suggestedTopics.filter((_, i) => i !== index);
    setSuggestedTopics(updated);
    setSelectedTopics(updated.map(t => t.name));
    saveSession(); // асинхронно
  };

  const handleAddCustomTopic = async () => {
    if (!customTopicName.trim()) {
      setError('Введите название темы');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/api/admin/ai/topics/describe', {
        domain,
        topic_name: customTopicName.trim(),
      });
      const newTopic = response.data; // { name, description }
      setSuggestedTopics([...suggestedTopics, newTopic]);
      setSelectedTopics([...selectedTopics, newTopic.name]);
      setCustomTopicName('');
      setIsAddingCustom(false);
      await saveSession();
    } catch (err: any) {
      console.error('Failed to describe custom topic:', err);
      setError(err.response?.data?.detail || 'Ошибка при добавлении темы');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateContent = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.post('/api/admin/ai/topics/generate-content', {
        domain,
        topics: selectedTopics,
      });
      setGeneratedContent(response.data.items);
      setStep('content');
      await saveSession();
    } catch (err: any) {
      console.error('Failed to generate content:', err);
      setError(err.response?.data?.detail || 'Ошибка при генерации контента');
    } finally {
      setLoading(false);
    }
  };

  const handleContentChange = (index: number, newContent: string) => {
    const updated = [...generatedContent];
    updated[index] = { ...updated[index], content: newContent };
    setGeneratedContent(updated);
  };

  const handleApprove = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.post('/api/admin/ai/topics/approve', {
        domain,
        topics: generatedContent.map(item => ({ name: item.name, content: item.content })),
      });
      setStep('done');
      await saveSession();
      setTimeout(() => navigate('/admin/drafts'), 3000);
    } catch (err: any) {
      console.error('Failed to approve topics:', err);
      setError(err.response?.data?.detail || 'Ошибка при утверждении тем');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveClick = () => {
    saveSession();
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-3xl font-bold text-gray-900">Подбор тем</h1>
          <div className="flex gap-2">
            {step !== 'input' && (
              <button
                onClick={handleSaveClick}
                className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Сохранить
              </button>
            )}
            <Link
              to="/admin/saved-topics"
              className="px-3 py-1 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              Сохранённые
            </Link>
          </div>
        </div>

        {savedMessage && (
          <div className="mb-4 p-2 bg-green-100 text-green-700 rounded text-center">
            {savedMessage}
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">{error}</div>
        )}

        {loading && <Loader />}

        {!loading && step === 'input' && (
          <div className="bg-white shadow-lg rounded-lg p-6">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Домен
              </label>
              <input
                type="text"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="например, Ритейл"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Роль (опционально)
              </label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="аналитик"
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            <button
              onClick={handleSuggest}
              disabled={loading}
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:bg-indigo-300"
            >
              {loading ? 'Подбор...' : 'Подобрать темы'}
            </button>
          </div>
        )}

        {!loading && step === 'suggestions' && (
          <div className="space-y-6">
            {suggestedTopics.map((topic, idx) => (
              <div key={idx} className="bg-white shadow rounded-lg p-4">
                <div className="flex items-start gap-4">
                  <div className="flex-1">
                    <input
                      type="text"
                      value={topic.name}
                      onChange={(e) => handleTopicNameChange(idx, e.target.value)}
                      className="text-lg font-semibold w-full border-b border-gray-300 focus:outline-none focus:border-indigo-500 pb-1 mb-2"
                    />
                    <p className="text-gray-600 text-sm">{topic.description}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRegenerateTopic(idx)}
                      className="text-sm text-indigo-600 hover:text-indigo-800"
                    >
                      Заменить
                    </button>
                    <button
                      onClick={() => handleDeleteTopic(idx)}
                      className="text-sm text-red-600 hover:text-red-800"
                    >
                      Удалить
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {/* Интерфейс добавления своей темы */}
            <div className="bg-white shadow rounded-lg p-4">
              {!isAddingCustom ? (
                <button
                  onClick={() => setIsAddingCustom(true)}
                  className="text-indigo-600 hover:text-indigo-800"
                >
                  + Добавить свою тему
                </button>
              ) : (
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={customTopicName}
                    onChange={(e) => setCustomTopicName(e.target.value)}
                    placeholder="Название темы"
                    className="flex-1 border border-gray-300 rounded-md px-3 py-2"
                  />
                  <button
                    onClick={handleAddCustomTopic}
                    disabled={loading}
                    className="px-3 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:bg-indigo-300"
                  >
                    Добавить
                  </button>
                  <button
                    onClick={() => setIsAddingCustom(false)}
                    className="px-3 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                  >
                    Отмена
                  </button>
                </div>
              )}
            </div>

            <div className="flex justify-end gap-4">
              <button
                onClick={() => setStep('input')}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Назад
              </button>
              <button
                onClick={handleGenerateContent}
                disabled={loading}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:bg-indigo-300"
              >
                {loading ? 'Генерация...' : 'Сгенерировать материалы'}
              </button>
            </div>
          </div>
        )}

        {!loading && step === 'content' && (
          <div className="space-y-6">
            {generatedContent.map((item, idx) => (
              <div key={idx} className="bg-white shadow rounded-lg p-4">
                <h3 className="text-lg font-semibold mb-2">{item.name}</h3>
                <textarea
                  value={item.content}
                  onChange={(e) => handleContentChange(idx, e.target.value)}
                  rows={10}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 font-mono text-sm"
                />
              </div>
            ))}
            <div className="flex justify-end gap-4">
              <button
                onClick={() => setStep('suggestions')}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Назад
              </button>
              <button
                onClick={handleApprove}
                disabled={loading}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300"
              >
                {loading ? 'Обработка...' : 'Утвердить и создать материалы'}
              </button>
            </div>
          </div>
        )}

        {step === 'done' && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
            <p className="text-green-700 mb-4">Темы успешно обработаны. Перенаправление к черновикам...</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default TopicSuggester;