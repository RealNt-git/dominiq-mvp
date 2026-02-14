// frontend/src/pages/admin/DraftList.tsx
// Страница списка черновиков терминов (методолог)
// Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0
// Обновлено: добавлена поддержка DELETE-эндпоинта и получение списка документов

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

interface DraftTerm {
  id: number;
  document_id: number;
  term: string;
  definition: string | null;
  example: string | null;
  context: string | null;
  status: string; // 'new', 'edited', 'approved', 'rejected'
  created_at: string;
  updated_at: string | null;
}

interface Document {
  id: number;
  filename: string;
  domain: string;
  processed: boolean;
}

const DraftList: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | 'all'>('all');
  const [drafts, setDrafts] = useState<DraftTerm[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [editingDraft, setEditingDraft] = useState<DraftTerm | null>(null);
  const [editForm, setEditForm] = useState({
    term: '',
    definition: '',
    example: '',
  });
  const [showModal, setShowModal] = useState(false);

  // Загрузка списка документов при монтировании
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Загрузка черновиков при изменении выбранного документа
  useEffect(() => {
    if (selectedDocId) {
      fetchDrafts();
    }
  }, [selectedDocId]);

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/api/admin/ai/documents');
      setDocuments(response.data);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      // Если эндпоинт недоступен, просто продолжаем работу без списка документов
      setDocuments([]);
    }
  };

  const fetchDrafts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {};
      if (selectedDocId !== 'all') {
        params.document_id = selectedDocId;
      }
      const response = await api.get('/api/admin/ai/drafts', { params });
      setDrafts(response.data);
    } catch (err) {
      console.error('Failed to fetch drafts:', err);
      setError('Не удалось загрузить черновики');
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = (draft: DraftTerm) => {
    setEditingDraft(draft);
    setEditForm({
      term: draft.term,
      definition: draft.definition || '',
      example: draft.example || '',
    });
    setShowModal(true);
  };

  const handleEditSave = async () => {
    if (!editingDraft) return;
    try {
      await api.put(`/api/admin/ai/drafts/${editingDraft.id}`, editForm);
      setSuccessMessage('Черновик успешно обновлён');
      fetchDrafts();
      setShowModal(false);
      setEditingDraft(null);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to update draft:', err);
      setError('Ошибка при сохранении');
    }
  };

  const handleDelete = async (draftId: number) => {
    if (!confirm('Вы уверены, что хотите удалить этот черновик?')) return;
    try {
      await api.delete(`/api/admin/ai/drafts/${draftId}`);
      setSuccessMessage('Черновик удалён');
      fetchDrafts();
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to delete draft:', err);
      setError('Ошибка при удалении');
    }
  };

  const handleApproveAll = async () => {
    if (!selectedDocId || selectedDocId === 'all') {
      setError('Выберите конкретный документ для утверждения');
      return;
    }
    try {
      await api.post('/api/admin/ai/drafts/approve', { document_id: selectedDocId });
      setSuccessMessage('Черновики утверждены');
      fetchDrafts(); // обновить список (статусы изменятся)
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to approve drafts:', err);
      setError('Ошибка при утверждении');
    }
  };

  const handleExport = async (format: 'json' | 'csv') => {
    if (!selectedDocId || selectedDocId === 'all') {
      setError('Выберите конкретный документ для экспорта');
      return;
    }
    try {
      const response = await api.get(`/api/admin/ai/export/${selectedDocId}?format=${format}`, {
        responseType: 'blob',
      });
      // Создаём ссылку для скачивания
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `drafts_${selectedDocId}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error('Export failed:', err);
      setError('Ошибка при экспорте');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-3xl font-bold text-gray-900">Черновики терминов</h1>
          <div className="flex gap-2">
            <Link
              to="/admin/upload"
              className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
            >
              Загрузить новый документ
            </Link>
            <Link
              to="/dashboard"
              className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              На главную
            </Link>
          </div>
        </div>

        {/* Фильтр по документу */}
        <div className="mb-6 flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Документ:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value === 'all' ? 'all' : Number(e.target.value))}
            className="mt-1 block w-64 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="all">Все документы</option>
            {documents.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.filename} ({doc.domain})
              </option>
            ))}
          </select>
          <button
            onClick={fetchDrafts}
            className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
          >
            Обновить
          </button>
        </div>

        {/* Кнопки действий */}
        <div className="mb-6 flex gap-2">
          <button
            onClick={handleApproveAll}
            disabled={selectedDocId === 'all'}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-green-300 disabled:cursor-not-allowed"
          >
            Утвердить все (для выбранного документа)
          </button>
          <button
            onClick={() => handleExport('json')}
            disabled={selectedDocId === 'all'}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
          >
            Экспорт JSON
          </button>
          <button
            onClick={() => handleExport('csv')}
            disabled={selectedDocId === 'all'}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-blue-300"
          >
            Экспорт CSV
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">{error}</div>
        )}
        {successMessage && (
          <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-md">{successMessage}</div>
        )}

        {loading ? (
          <div className="text-center py-8">Загрузка...</div>
        ) : (
          <div className="bg-white shadow-lg rounded-lg overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Термин
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Определение
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Статус
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {drafts.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                      Нет черновиков
                    </td>
                  </tr>
                ) : (
                  drafts.map((draft) => (
                    <tr key={draft.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {draft.term}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">
                        {draft.definition}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span
                          className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            draft.status === 'approved'
                              ? 'bg-green-100 text-green-800'
                              : draft.status === 'rejected'
                              ? 'bg-red-100 text-red-800'
                              : draft.status === 'edited'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {draft.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button
                          onClick={() => handleEditClick(draft)}
                          className="text-indigo-600 hover:text-indigo-900 mr-3"
                        >
                          Редактировать
                        </button>
                        <button
                          onClick={() => handleDelete(draft.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Удалить
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Модальное окно редактирования */}
      {showModal && editingDraft && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center">
          <div className="relative bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Редактировать черновик</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Термин</label>
                <input
                  type="text"
                  value={editForm.term}
                  onChange={(e) => setEditForm({ ...editForm, term: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Определение</label>
                <textarea
                  value={editForm.definition}
                  onChange={(e) => setEditForm({ ...editForm, definition: e.target.value })}
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Пример</label>
                <textarea
                  value={editForm.example}
                  onChange={(e) => setEditForm({ ...editForm, example: e.target.value })}
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Контекст (только для просмотра)</label>
                <textarea
                  value={editingDraft.context || ''}
                  readOnly
                  rows={2}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50"
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
              >
                Отмена
              </button>
              <button
                onClick={handleEditSave}
                className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
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

export default DraftList;