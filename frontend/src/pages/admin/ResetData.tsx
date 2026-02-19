///frontend/src/pages/admin/ResetData.tsx
import React, { useState } from 'react';
import api from '../../services/api';

const ResetData: React.FC = () => {
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleReset = async () => {
    if (confirm !== 'RESET') {
      alert('Введите RESET для подтверждения');
      return;
    }
    setLoading(true);
    try {
      const response = await api.post('/api/admin/reset-data', null, {
        params: { confirmation: 'RESET' }
      });
      setResult(response.data);
    } catch (error) {
      console.error('Reset failed', error);
      alert('Ошибка сброса данных');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 border border-red-300 rounded">
      <h2 className="text-xl font-bold mb-4 text-red-600">Сброс базы данных</h2>
      <p className="mb-2">Это удалит все документы, термины, квизы, прогресс и т.д. Пользователи останутся.</p>
      <p className="mb-2">Введите <strong>RESET</strong> для подтверждения:</p>
      <input
        type="text"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        className="border p-2 mr-2"
        placeholder="RESET"
      />
      <button
        onClick={handleReset}
        disabled={loading || confirm !== 'RESET'}
        className="bg-red-600 text-white px-4 py-2 rounded disabled:opacity-50"
      >
        {loading ? 'Сброс...' : 'Очистить все данные'}
      </button>
      {result && (
        <pre className="mt-4 p-2 bg-gray-100 text-sm">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
};

export default ResetData;