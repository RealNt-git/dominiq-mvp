// frontend/src/pages/admin/PlanManager.tsx
// Страница управления планами развития с фильтрацией тем по домену

import React, { useEffect, useState } from 'react';
import api from '../../services/api';

interface User {
  id: number;
  email: string;
}

interface Domain {
  id: number;
  name: string;
}

interface Topic {
  id: number;
  name: string;
  domain_id: number;
}

interface Grade {
  id: number;
  name: string;
  description?: string;
}

interface Plan {
  id: number;
  user_id: number;
  topic_id: number;
  grade_id: number;
  priority: number;
  target_date: string | null;
  status: string;
  topic?: Topic;
  grade?: Grade;
}

const PlanManager: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [grades, setGrades] = useState<Grade[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedUserId, setSelectedUserId] = useState<number | ''>('');
  const [plans, setPlans] = useState<Plan[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');

  // Состояния для фильтрации тем по домену в форме создания
  const [selectedDomainId, setSelectedDomainId] = useState<number | ''>('');

  // Состояние формы создания нового плана
  const [newPlan, setNewPlan] = useState({
    topic_id: '',
    grade_id: '',
    priority: 1,
    target_date: '',
    status: 'active',
  });

  const [editingPlan, setEditingPlan] = useState<Plan | null>(null);
  const [editForm, setEditForm] = useState({
    topic_id: '',
    grade_id: '',
    priority: 1,
    target_date: '',
    status: 'active',
  });

  // Загрузка справочных данных при монтировании
  useEffect(() => {
    const fetchReferences = async () => {
      setLoading(true);
      setError(null);
      try {
        const [usersRes, domainsRes, topicsRes, gradesRes] = await Promise.all([
          api.get('/api/plan/plans/users'),
          api.get('/api/domains'),
          api.get('/api/plan/plans/topics'),
          api.get('/api/plan/plans/grades'),
        ]);
        setUsers(usersRes.data);
        setDomains(domainsRes.data);
        setTopics(topicsRes.data);
        setGrades(gradesRes.data);
      } catch (err) {
        console.error('Failed to fetch references:', err);
        setError('Не удалось загрузить справочные данные');
      } finally {
        setLoading(false);
      }
    };
    fetchReferences();
  }, []);

  // Загрузка планов при выборе пользователя
  useEffect(() => {
    if (!selectedUserId) {
      setPlans([]);
      return;
    }
    const fetchPlans = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await api.get(`/api/plan/plans/?user_id=${selectedUserId}`);
        setPlans(res.data);
      } catch (err) {
        console.error('Failed to fetch plans:', err);
        setError('Не удалось загрузить планы');
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, [selectedUserId]);

  // Фильтрация тем по выбранному домену для формы создания
  const topicsForDomain = selectedDomainId
    ? topics.filter(t => t.domain_id === selectedDomainId)
    : [];

  // Обработчики для формы создания
  const handleNewPlanChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setNewPlan({ ...newPlan, [name]: value });
  };

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserId) {
      setError('Выберите пользователя');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const payload = {
        user_id: selectedUserId,
        topic_id: parseInt(newPlan.topic_id),
        grade_id: parseInt(newPlan.grade_id),
        priority: newPlan.priority,
        target_date: newPlan.target_date || null,
        status: newPlan.status,
      };
      await api.post('/api/plan/plans/', payload);
      // Обновить список планов
      const res = await api.get(`/api/plan/plans/?user_id=${selectedUserId}`);
      setPlans(res.data);
      setNewPlan({
        topic_id: '',
        grade_id: '',
        priority: 1,
        target_date: '',
        status: 'active',
      });
      setSelectedDomainId('');
    } catch (err: any) {
      console.error('Failed to create plan:', err);
      setError(err.response?.data?.detail || 'Ошибка при создании плана');
    } finally {
      setLoading(false);
    }
  };

  const openEditModal = (plan: Plan) => {
    setEditingPlan(plan);
    setEditForm({
      topic_id: plan.topic_id.toString(),
      grade_id: plan.grade_id.toString(),
      priority: plan.priority,
      target_date: plan.target_date || '',
      status: plan.status,
    });
  };

  const handleEditChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setEditForm({ ...editForm, [name]: value });
  };

  const handleUpdatePlan = async () => {
    if (!editingPlan) return;
    setLoading(true);
    setError(null);
    try {
      const payload = {
        topic_id: parseInt(editForm.topic_id),
        grade_id: parseInt(editForm.grade_id),
        priority: editForm.priority,
        target_date: editForm.target_date || null,
        status: editForm.status,
      };
      await api.put(`/api/plan/plans/${editingPlan.id}`, payload);
      const res = await api.get(`/api/plan/plans/?user_id=${selectedUserId}`);
      setPlans(res.data);
      setEditingPlan(null);
    } catch (err: any) {
      console.error('Failed to update plan:', err);
      setError(err.response?.data?.detail || 'Ошибка при обновлении плана');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePlan = async (planId: number) => {
    if (!window.confirm('Удалить этот план?')) return;
    setLoading(true);
    setError(null);
    try {
      await api.delete(`/api/plan/plans/${planId}`);
      const res = await api.get(`/api/plan/plans/?user_id=${selectedUserId}`);
      setPlans(res.data);
    } catch (err: any) {
      console.error('Failed to delete plan:', err);
      setError(err.response?.data?.detail || 'Ошибка при удалении плана');
    } finally {
      setLoading(false);
    }
  };

  const getTopicName = (topicId: number) => topics.find(t => t.id === topicId)?.name || `Тема ${topicId}`;
  const getGradeName = (gradeId: number) => grades.find(g => g.id === gradeId)?.name || `Грейд ${gradeId}`;

  const filteredPlans = plans.filter(plan => {
    if (filterStatus === 'all') return true;
    return plan.status === filterStatus;
  });

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Управление планами развития</h1>

        {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">{error}</div>}

        <div className="mb-6 bg-white p-4 rounded shadow">
          <label htmlFor="userSelect" className="block text-sm font-medium text-gray-700 mb-2">
            Выберите пользователя:
          </label>
          <select
            id="userSelect"
            value={selectedUserId}
            onChange={(e) => setSelectedUserId(e.target.value ? Number(e.target.value) : '')}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="">-- Выберите пользователя --</option>
            {users.map(user => (
              <option key={user.id} value={user.id}>{user.email}</option>
            ))}
          </select>
        </div>

        {selectedUserId && (
          <div className="mb-6 bg-white p-4 rounded shadow">
            <h2 className="text-xl font-semibold mb-4">Назначить новый план</h2>
            <form onSubmit={handleCreatePlan} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {/* Выбор домена */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Домен</label>
                <select
                  name="domain_id"
                  value={selectedDomainId}
                  onChange={(e) => setSelectedDomainId(e.target.value ? Number(e.target.value) : '')}
                  required
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  <option value="">-- Выберите домен --</option>
                  {domains.map(domain => (
                    <option key={domain.id} value={domain.id}>{domain.name}</option>
                  ))}
                </select>
              </div>
              {/* Выбор темы (зависит от домена) */}
              <div>
                <label className="block text-sm font-medium text-gray-700">Тема</label>
                <select
                  name="topic_id"
                  value={newPlan.topic_id}
                  onChange={handleNewPlanChange}
                  required
                  disabled={!selectedDomainId}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md disabled:bg-gray-100"
                >
                  <option value="">-- Выберите тему --</option>
                  {topicsForDomain.map(topic => (
                    <option key={topic.id} value={topic.id}>{topic.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Грейд</label>
                <select
                  name="grade_id"
                  value={newPlan.grade_id}
                  onChange={handleNewPlanChange}
                  required
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  <option value="">-- Выберите грейд --</option>
                  {grades.map(grade => (
                    <option key={grade.id} value={grade.id}>{grade.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Приоритет (1 - наивысший)</label>
                <input
                  type="number"
                  name="priority"
                  min="1"
                  value={newPlan.priority}
                  onChange={handleNewPlanChange}
                  required
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Срок (необязательно)</label>
                <input
                  type="date"
                  name="target_date"
                  value={newPlan.target_date}
                  onChange={handleNewPlanChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div className="sm:col-span-2">
                <label className="block text-sm font-medium text-gray-700">Статус</label>
                <select
                  name="status"
                  value={newPlan.status}
                  onChange={handleNewPlanChange}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  <option value="active">Активен</option>
                  <option value="completed">Завершён</option>
                  <option value="archived">Архивирован</option>
                </select>
              </div>
              <div className="sm:col-span-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300"
                >
                  {loading ? 'Сохранение...' : 'Назначить'}
                </button>
              </div>
            </form>
          </div>
        )}

        {selectedUserId && (
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="px-4 py-5 sm:px-6 flex justify-between items-center">
              <h3 className="text-lg leading-6 font-medium text-gray-900">Текущие планы пользователя</h3>
              <div className="flex items-center space-x-2">
                <label htmlFor="statusFilter" className="text-sm text-gray-600">Фильтр по статусу:</label>
                <select
                  id="statusFilter"
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="block w-40 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  <option value="all">Все</option>
                  <option value="active">Активные</option>
                  <option value="completed">Завершённые</option>
                  <option value="archived">Архивированные</option>
                </select>
              </div>
            </div>
            {loading && <div className="p-4 text-center">Загрузка...</div>}
            {!loading && filteredPlans.length === 0 && (
              <div className="p-4 text-center text-gray-500">Планов с выбранным статусом нет</div>
            )}
            {!loading && filteredPlans.length > 0 && (
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Тема</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Грейд</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Приоритет</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Срок</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Статус</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Действия</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredPlans.map((plan) => (
                    <tr key={plan.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {getTopicName(plan.topic_id)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {getGradeName(plan.grade_id)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {plan.priority}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {plan.target_date ? new Date(plan.target_date).toLocaleDateString('ru-RU') : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            plan.status === 'active' ? 'bg-green-100 text-green-800' :
                            plan.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {plan.status === 'active' ? 'Активен' :
                           plan.status === 'completed' ? 'Завершён' : 'Архивирован'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => openEditModal(plan)}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                        >
                          Редактировать
                        </button>
                        <button
                          onClick={() => handleDeletePlan(plan.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Удалить
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </div>

      {/* Модальное окно редактирования (без изменений) */}
      {editingPlan && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
          <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Редактировать план</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Тема</label>
                <select
                  name="topic_id"
                  value={editForm.topic_id}
                  onChange={handleEditChange}
                  required
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  {topics.map(topic => (
                    <option key={topic.id} value={topic.id}>{topic.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Грейд</label>
                <select
                  name="grade_id"
                  value={editForm.grade_id}
                  onChange={handleEditChange}
                  required
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  {grades.map(grade => (
                    <option key={grade.id} value={grade.id}>{grade.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Приоритет</label>
                <input
                  type="number"
                  name="priority"
                  min="1"
                  value={editForm.priority}
                  onChange={handleEditChange}
                  required
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Срок (необязательно)</label>
                <input
                  type="date"
                  name="target_date"
                  value={editForm.target_date}
                  onChange={handleEditChange}
                  className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Статус</label>
                <select
                  name="status"
                  value={editForm.status}
                  onChange={handleEditChange}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                >
                  <option value="active">Активен</option>
                  <option value="completed">Завершён</option>
                  <option value="archived">Архивирован</option>
                </select>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setEditingPlan(null)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Отмена
              </button>
              <button
                onClick={handleUpdatePlan}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
                disabled={loading}
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PlanManager;