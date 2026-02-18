// frontend/src/pages/admin/TermManager.tsx
// Управление утверждёнными терминами (CRUD) для методолога
// Отображает список терминов, каждый с вложенными вопросами.

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

interface Domain {
  id: number;
  name: string;
}

interface Topic {
  id: number;
  name: string;
  domain_id: number;
}

// Интерфейс вопроса (QuestionOut)
interface Question {
  id: number;
  quiz_id: number;
  term_id: number;
  text: string;
  type: string;
  options: string[] | null;
  correct_answer: any; // может быть числом, массивом, строкой или объектом
  explanation: string | null;
}

// Интерфейс термина с вопросами (TermWithQuestions)
interface Term {
  id: number;
  term: string;
  definition: string;
  example: string | null;
  mnemonic: string | null;
  image_url: string | null;
  domain_id: number;
  topic_id: number | null;
  source_document: string | null;
  created_at: string;
  questions?: Question[]; // вложенные вопросы
}

const TermManager: React.FC = () => {
  const [terms, setTerms] = useState<Term[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingTerm, setEditingTerm] = useState<Term | null>(null);
  const [formData, setFormData] = useState({
    term: '',
    definition: '',
    example: '',
    mnemonic: '',
    image_url: '',
    domain_id: 0,
    topic_id: '',
  });

  // Фильтры
  const [filterDomain, setFilterDomain] = useState<number | ''>('');
  const [filterTopic, setFilterTopic] = useState<number | ''>('');

  // Загрузка доменов и тем при монтировании
  useEffect(() => {
    fetchDomains();
    fetchTopics();
  }, []);

  // Загрузка терминов при изменении фильтров
  useEffect(() => {
    fetchTerms();
  }, [filterDomain, filterTopic]);

  const fetchDomains = async () => {
    try {
      const response = await api.get('/api/domains');
      setDomains(response.data);
      if (response.data.length > 0) {
        setFormData(prev => ({ ...prev, domain_id: response.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to fetch domains:', err);
    }
  };

  const fetchTopics = async () => {
    try {
      const response = await api.get('/api/topics');
      setTopics(response.data);
    } catch (err) {
      console.error('Failed to fetch topics:', err);
    }
  };

  const fetchTerms = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {};
      if (filterDomain) params.domain_id = filterDomain;
      if (filterTopic) params.topic_id = filterTopic;
      const response = await api.get('/api/terms', { params });
      setTerms(response.data); // ожидаем массив TermWithQuestions
    } catch (err) {
      console.error('Failed to fetch terms:', err);
      setError('Не удалось загрузить термины');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData({ ...formData, [name]: value });
  };

  const resetForm = () => {
    setFormData({
      term: '',
      definition: '',
      example: '',
      mnemonic: '',
      image_url: '',
      domain_id: domains[0]?.id || 0,
      topic_id: '',
    });
    setEditingTerm(null);
  };

  const handleAdd = () => {
    resetForm();
    setShowModal(true);
  };

  const handleEdit = (term: Term) => {
    setEditingTerm(term);
    setFormData({
      term: term.term,
      definition: term.definition,
      example: term.example || '',
      mnemonic: term.mnemonic || '',
      image_url: term.image_url || '',
      domain_id: term.domain_id,
      topic_id: term.topic_id?.toString() || '',
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Вы уверены, что хотите удалить этот термин? Все связанные вопросы также будут удалены.')) return;
    try {
      await api.delete(`/api/terms/${id}`);
      fetchTerms();
    } catch (err) {
      console.error('Failed to delete term:', err);
      setError('Ошибка при удалении');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      ...formData,
      topic_id: formData.topic_id ? parseInt(formData.topic_id) : null,
    };
    try {
      if (editingTerm) {
        await api.put(`/api/terms/${editingTerm.id}`, payload);
      } else {
        await api.post('/api/terms', payload);
      }
      setShowModal(false);
      fetchTerms();
    } catch (err) {
      console.error('Failed to save term:', err);
      setError('Ошибка при сохранении');
    }
  };

  // Фильтрация тем по выбранному домену для выпадающего списка
  const filteredTopics = topics.filter(t => t.domain_id === formData.domain_id);

  // Вспомогательная функция для форматирования правильного ответа
  const formatCorrectAnswer = (answer: any): string => {
    if (answer === null || answer === undefined) return '—';
    if (typeof answer === 'object') return JSON.stringify(answer);
    return String(answer);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Управление терминами и вопросами</h1>
          <div className="flex gap-2">
            <button
              onClick={handleAdd}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
            >
              Добавить термин
            </button>
            <Link
              to="/dashboard"
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              На главную
            </Link>
          </div>
        </div>

        {/* Фильтры */}
        <div className="mb-6 flex gap-4 items-end bg-white p-4 rounded-lg shadow">
          <div>
            <label className="block text-sm font-medium text-gray-700">Домен</label>
            <select
              value={filterDomain}
              onChange={(e) => setFilterDomain(e.target.value ? parseInt(e.target.value) : '' )}
              className="mt-1 block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="">Все</option>
              {domains.map(d => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Тема</label>
            <select
              value={filterTopic}
              onChange={(e) => setFilterTopic(e.target.value ? parseInt(e.target.value) : '' )}
              className="mt-1 block w-48 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
            >
              <option value="">Все</option>
              {topics.map(t => (
                <option key={t.id} value={t.id}>{t.name}</option>
              ))}
            </select>
          </div>
          <button
            onClick={() => { setFilterDomain(''); setFilterTopic(''); }}
            className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            Сбросить
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">{error}</div>
        )}

        {loading ? (
          <div className="text-center py-8">Загрузка...</div>
        ) : (
          <div className="bg-white shadow-lg rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Термин</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Определение</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Домен</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Тема</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Действия</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {terms.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                      Нет терминов
                    </td>
                  </tr>
                ) : (
                  terms.flatMap((term) => {
                    const domain = domains.find(d => d.id === term.domain_id);
                    const topic = topics.find(t => t.id === term.topic_id);
                    // Строка термина
                    const termRow = (
                      <tr key={term.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {term.term}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">
                          {term.definition}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {domain?.name || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {topic?.name || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <button
                            onClick={() => handleEdit(term)}
                            className="text-indigo-600 hover:text-indigo-900 mr-3"
                          >
                            Редактировать
                          </button>
                          <button
                            onClick={() => handleDelete(term.id)}
                            className="text-red-600 hover:text-red-900"
                          >
                            Удалить
                          </button>
                        </td>
                      </tr>
                    );

                    // Строка с вопросами (если они есть)
                    const questionsRows = term.questions && term.questions.length > 0 ? (
                      <tr key={`q-${term.id}`} className="bg-gray-50">
                        <td colSpan={5} className="px-6 py-4">
                          <div className="text-sm font-medium text-gray-700 mb-2">Вопросы по термину:</div>
                          <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-100">
                              <tr>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Вопрос</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Варианты</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Правильный ответ</th>
                                <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Пояснение</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                              {term.questions.map((q) => (
                                <tr key={q.id}>
                                  <td className="px-4 py-2 text-sm text-gray-900 max-w-xs truncate">{q.text}</td>
                                  <td className="px-4 py-2 text-sm text-gray-500">
                                    {q.options ? JSON.stringify(q.options) : '—'}
                                  </td>
                                  <td className="px-4 py-2 text-sm text-gray-500">
                                    {formatCorrectAnswer(q.correct_answer)}
                                  </td>
                                  <td className="px-4 py-2 text-sm text-gray-500 max-w-xs truncate">{q.explanation || '—'}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </td>
                      </tr>
                    ) : null;

                    return questionsRows ? [termRow, questionsRows] : [termRow];
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Модальное окно добавления/редактирования термина (без изменений) */}
      {showModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
          <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              {editingTerm ? 'Редактировать термин' : 'Добавить термин'}
            </h3>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Термин *</label>
                <input
                  type="text"
                  name="term"
                  value={formData.term}
                  onChange={handleInputChange}
                  required
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Определение *</label>
                <textarea
                  name="definition"
                  value={formData.definition}
                  onChange={handleInputChange}
                  required
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Пример</label>
                <textarea
                  name="example"
                  value={formData.example}
                  onChange={handleInputChange}
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Мнемоника</label>
                <input
                  type="text"
                  name="mnemonic"
                  value={formData.mnemonic}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">URL изображения</label>
                <input
                  type="url"
                  name="image_url"
                  value={formData.image_url}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Домен *</label>
                <select
                  name="domain_id"
                  value={formData.domain_id}
                  onChange={handleInputChange}
                  required
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  {domains.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Тема</label>
                <select
                  name="topic_id"
                  value={formData.topic_id}
                  onChange={handleInputChange}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="">Без темы</option>
                  {filteredTopics.map(t => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </select>
              </div>
              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                >
                  {editingTerm ? 'Сохранить' : 'Создать'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default TermManager;