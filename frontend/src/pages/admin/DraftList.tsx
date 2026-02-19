// frontend/src/pages/admin/DraftList.tsx
// Страница управления черновиками терминов с вопросами (методолог)
// Отображает список черновиков терминов, каждый с вложенными черновиками вопросов.
// Позволяет редактировать и удалять термины и вопросы, утверждать все черновики документа.

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../services/api';

interface Document {
  id: number;
  filename: string;
  domain: string;
  processed: boolean;
}

interface DraftQuestion {
  id: number;
  document_id: number;
  term_id: number;
  question: string;
  options: string[] | null;
  correct: number;
  explanation: string | null;
  status: string;
  created_at: string;
}

interface DraftTerm {
  id: number;
  document_id: number;
  term: string;
  definition: string | null;
  example: string | null;
  context: string | null;
  mnemonic: string | null;
  status: string;
  created_at: string;
  updated_at: string | null;
  questions: DraftQuestion[];
}

const DraftList: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<number | 'all'>('all');
  const [terms, setTerms] = useState<DraftTerm[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Состояние для редактирования термина
  const [editingTerm, setEditingTerm] = useState<DraftTerm | null>(null);
  const [termEditForm, setTermEditForm] = useState({
    term: '',
    definition: '',
    example: '',
    mnemonic: '',
  });
  const [showTermModal, setShowTermModal] = useState(false);

  // Состояние для редактирования вопроса
  const [editingQuestion, setEditingQuestion] = useState<DraftQuestion | null>(null);
  const [questionEditForm, setQuestionEditForm] = useState({
    question: '',
    options: '',
    correct: 0,
    explanation: '',
  });
  const [showQuestionModal, setShowQuestionModal] = useState(false);

  useEffect(() => {
    fetchDocuments();
  }, []);

  useEffect(() => {
    fetchTermsWithQuestions();
  }, [selectedDocId]);

  const fetchDocuments = async () => {
    try {
      const response = await api.get('/api/admin/ai/documents');
      setDocuments(response.data);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      setDocuments([]);
    }
  };

  const fetchTermsWithQuestions = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: any = {};
      if (selectedDocId !== 'all') {
        params.document_id = selectedDocId;
      }
      const response = await api.get('/api/admin/ai/drafts/with-questions', { params });
      setTerms(response.data);
    } catch (err) {
      console.error('Failed to fetch drafts:', err);
      setError('Не удалось загрузить черновики');
    } finally {
      setLoading(false);
    }
  };

  const handleEditTermClick = (term: DraftTerm) => {
    setEditingTerm(term);
    setTermEditForm({
      term: term.term,
      definition: term.definition || '',
      example: term.example || '',
      mnemonic: term.mnemonic || '',
    });
    setShowTermModal(true);
  };

  const handleTermEditSave = async () => {
    if (!editingTerm) return;
    try {
      await api.put(`/api/admin/ai/drafts/${editingTerm.id}`, termEditForm);
      setSuccessMessage('Термин обновлён');
      fetchTermsWithQuestions();
      setShowTermModal(false);
      setEditingTerm(null);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to update term:', err);
      setError('Ошибка при сохранении термина');
    }
  };

  const handleDeleteTerm = async (termId: number) => {
    if (!window.confirm('Удалить этот термин? Все связанные вопросы также будут удалены.')) return;
    try {
      await api.delete(`/api/admin/ai/drafts/${termId}`);
      setSuccessMessage('Термин удалён');
      fetchTermsWithQuestions();
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to delete term:', err);
      setError('Ошибка при удалении термина');
    }
  };

  const handleEditQuestionClick = (question: DraftQuestion) => {
    setEditingQuestion(question);
    setQuestionEditForm({
      question: question.question,
      options: question.options ? JSON.stringify(question.options) : '',
      correct: question.correct,
      explanation: question.explanation || '',
    });
    setShowQuestionModal(true);
  };

  const handleQuestionEditSave = async () => {
    if (!editingQuestion) return;
    try {
      let options = null;
      if (questionEditForm.options.trim()) {
        try {
          options = JSON.parse(questionEditForm.options);
        } catch {
          setError('Ошибка: варианты ответов должны быть в формате JSON массива');
          return;
        }
      }
      const payload = {
        question: questionEditForm.question,
        options,
        correct: questionEditForm.correct,
        explanation: questionEditForm.explanation || null,
      };
      await api.put(`/api/admin/ai/draft-questions/${editingQuestion.id}`, payload);
      setSuccessMessage('Вопрос обновлён');
      fetchTermsWithQuestions();
      setShowQuestionModal(false);
      setEditingQuestion(null);
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to update question:', err);
      setError('Ошибка при сохранении вопроса');
    }
  };

  const handleDeleteQuestion = async (questionId: number) => {
    if (!window.confirm('Удалить этот вопрос?')) return;
    try {
      await api.delete(`/api/admin/ai/draft-questions/${questionId}`);
      setSuccessMessage('Вопрос удалён');
      fetchTermsWithQuestions();
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to delete question:', err);
      setError('Ошибка при удалении вопроса');
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
      fetchTermsWithQuestions();
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

  const getDocumentName = (docId: number): string => {
    const doc = documents.find(d => d.id === docId);
    return doc ? doc.filename : `Документ ${docId}`;
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-full mx-auto px-4">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-3xl font-bold text-gray-900">Черновики терминов и вопросов</h1>
          <div className="flex gap-2">
            <Link to="/admin/upload" className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
              Загрузить новый документ
            </Link>
            <Link to="/dashboard" className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">
              На главную
            </Link>
          </div>
        </div>

        <div className="mb-6 flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Документ:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value === 'all' ? 'all' : Number(e.target.value))}
            className="mt-1 block w-64 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="all">Все документы</option>
            {documents.map(doc => (
              <option key={doc.id} value={doc.id}>{doc.filename} ({doc.domain})</option>
            ))}
          </select>
          <button onClick={fetchTermsWithQuestions} className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300">
            Обновить
          </button>
        </div>

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

        {error && <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">{error}</div>}
        {successMessage && <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-md">{successMessage}</div>}

        {loading ? (
          <div className="text-center py-8">Загрузка...</div>
        ) : (
          // Добавляем горизонтальную прокрутку для основной таблицы
          <div className="bg-white shadow-lg rounded-lg overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Термин</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Определение</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Документ</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Действия</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {terms.length === 0 ? (
                  <tr><td colSpan={5} className="px-6 py-4 text-center text-gray-500">Нет черновиков</td></tr>
                ) : (
                  terms.flatMap(term => [
                    <tr key={term.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{term.term}</td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-md truncate">{term.definition}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{getDocumentName(term.document_id)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                          term.status === 'approved' ? 'bg-green-100 text-green-800' :
                          term.status === 'rejected' ? 'bg-red-100 text-red-800' :
                          term.status === 'edited' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {term.status === 'approved' ? 'Утверждён' :
                           term.status === 'rejected' ? 'Отклонён' :
                           term.status === 'edited' ? 'Отредактирован' : 'Новый'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button onClick={() => handleEditTermClick(term)} className="text-indigo-600 hover:text-indigo-900 mr-3">Ред. термин</button>
                        <button onClick={() => handleDeleteTerm(term.id)} className="text-red-600 hover:text-red-900">Удалить термин</button>
                      </td>
                    </tr>,
                    term.questions && term.questions.length > 0 && (
                      <tr key={`q-${term.id}`} className="bg-gray-50">
                        <td colSpan={5} className="px-6 py-4">
                          <div className="text-sm font-medium text-gray-700 mb-2">Вопросы по термину:</div>
                          {/* Добавляем горизонтальную прокрутку для таблицы вопросов */}
                          <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200">
                              <thead className="bg-gray-100">
                                <tr>
                                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Вопрос</th>
                                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Варианты</th>
                                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Правильный</th>
                                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Пояснение</th>
                                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Статус</th>
                                  <th className="px-4 py-2 text-right text-xs font-medium text-gray-500 uppercase">Действия</th>
                                </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                {term.questions.map(q => (
                                  <tr key={q.id}>
                                    <td className="px-4 py-2 text-sm text-gray-900 max-w-xs truncate">{q.question}</td>
                                    <td className="px-4 py-2 text-sm text-gray-500">{q.options ? JSON.stringify(q.options) : '—'}</td>
                                    <td className="px-4 py-2 text-sm text-gray-500">{q.correct}</td>
                                    <td className="px-4 py-2 text-sm text-gray-500 max-w-xs truncate">{q.explanation || '—'}</td>
                                    <td className="px-4 py-2 whitespace-nowrap text-sm">
                                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                                        q.status === 'approved' ? 'bg-green-100 text-green-800' :
                                        q.status === 'rejected' ? 'bg-red-100 text-red-800' :
                                        q.status === 'edited' ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-gray-100 text-gray-800'
                                      }`}>{q.status}</span>
                                    </td>
                                    <td className="px-4 py-2 whitespace-nowrap text-right text-sm font-medium">
                                      <button onClick={() => handleEditQuestionClick(q)} className="text-indigo-600 hover:text-indigo-900 mr-2">Ред.</button>
                                      <button onClick={() => handleDeleteQuestion(q.id)} className="text-red-600 hover:text-red-900">Удалить</button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </td>
                      </tr>
                    )
                  ])
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Модальное окно редактирования термина */}
      {showTermModal && editingTerm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">Редактировать термин</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Термин</label>
                <input type="text" value={termEditForm.term} onChange={e => setTermEditForm({...termEditForm, term: e.target.value})} className="w-full border border-gray-300 rounded-md px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Определение</label>
                <textarea rows={3} value={termEditForm.definition} onChange={e => setTermEditForm({...termEditForm, definition: e.target.value})} className="w-full border border-gray-300 rounded-md px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Пример</label>
                <textarea rows={2} value={termEditForm.example} onChange={e => setTermEditForm({...termEditForm, example: e.target.value})} className="w-full border border-gray-300 rounded-md px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Мнемоника</label>
                <input type="text" value={termEditForm.mnemonic} onChange={e => setTermEditForm({...termEditForm, mnemonic: e.target.value})} className="w-full border border-gray-300 rounded-md px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Контекст (только просмотр)</label>
                <textarea value={editingTerm.context || ''} readOnly rows={2} className="w-full border border-gray-300 rounded-md px-3 py-2 bg-gray-50" />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setShowTermModal(false)} className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">Отмена</button>
              <button onClick={handleTermEditSave} className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">Сохранить</button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно редактирования вопроса */}
      {showQuestionModal && editingQuestion && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
            <h3 className="text-lg font-semibold mb-4">Редактировать вопрос</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Текст вопроса</label>
                <textarea rows={2} value={questionEditForm.question} onChange={e => setQuestionEditForm({...questionEditForm, question: e.target.value})} className="w-full border border-gray-300 rounded-md px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Варианты ответов (JSON массив)
                </label>
                <textarea rows={3} value={questionEditForm.options} onChange={e => setQuestionEditForm({...questionEditForm, options: e.target.value})} className="w-full border border-gray-300 rounded-md px-3 py-2 font-mono text-sm" placeholder='["Вариант 1", "Вариант 2", "Вариант 3", "Вариант 4"]' />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Индекс правильного ответа (0-3)</label>
                <input type="number" min="0" max="3" value={questionEditForm.correct} onChange={e => setQuestionEditForm({...questionEditForm, correct: parseInt(e.target.value) || 0})} className="w-full border border-gray-300 rounded-md px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Пояснение</label>
                <textarea rows={2} value={questionEditForm.explanation} onChange={e => setQuestionEditForm({...questionEditForm, explanation: e.target.value})} className="w-full border border-gray-300 rounded-md px-3 py-2" />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button onClick={() => setShowQuestionModal(false)} className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">Отмена</button>
              <button onClick={handleQuestionEditSave} className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">Сохранить</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DraftList;