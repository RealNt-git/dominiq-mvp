// frontend/src/pages/admin/TableViewer.tsx
import React, { useEffect, useState } from 'react';
import api from '../../services/api';

interface TableDataResponse {
  table_name: string;
  columns: string[];
  total: number;
  data: Record<string, any>[];
  limit: number;
  offset: number;
}

const TableViewer: React.FC = () => {
  const [tables, setTables] = useState<string[]>([]);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [data, setData] = useState<TableDataResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [limit] = useState(100);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    fetchTables();
  }, []);

  const fetchTables = async () => {
    try {
      const response = await api.get('/api/admin/tables');
      setTables(response.data.tables);
    } catch (err) {
      console.error('Failed to fetch tables:', err);
      setError('Не удалось загрузить список таблиц');
    }
  };

  const fetchTableData = async (table: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/api/admin/table/${table}`, {
        params: { limit, offset }
      });
      setData(response.data);
    } catch (err: any) {
      console.error('Failed to fetch table data:', err);
      setError(err.response?.data?.detail || 'Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const table = e.target.value;
    setSelectedTable(table);
    setOffset(0);
    if (table) {
      fetchTableData(table);
    } else {
      setData(null);
    }
  };

  const handlePrevPage = () => {
    if (offset - limit >= 0) {
      setOffset(offset - limit);
      fetchTableData(selectedTable);
    }
  };

  const handleNextPage = () => {
    if (data && offset + limit < data.total) {
      setOffset(offset + limit);
      fetchTableData(selectedTable);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Просмотр данных БД</h1>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">{error}</div>
        )}

        <div className="mb-6 flex items-center gap-4">
          <label className="text-sm font-medium text-gray-700">Таблица:</label>
          <select
            value={selectedTable}
            onChange={handleTableChange}
            className="mt-1 block w-64 pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
          >
            <option value="">-- Выберите таблицу --</option>
            {tables.map(table => (
              <option key={table} value={table}>{table}</option>
            ))}
          </select>
        </div>

        {loading && <div className="text-center py-8">Загрузка...</div>}

        {data && (
          <div className="bg-white shadow-lg rounded-lg overflow-hidden">
            <div className="px-4 py-3 bg-gray-100 border-b flex justify-between items-center">
              <span className="font-medium">Таблица: {data.table_name}</span>
              <span className="text-sm text-gray-600">
                Записи {data.offset + 1}–{Math.min(data.offset + data.limit, data.total)} из {data.total}
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {data.columns.map(col => (
                      <th key={col} className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.data.map((row, idx) => (
                    <tr key={idx}>
                      {data.columns.map(col => (
                        <td key={col} className="px-4 py-2 text-sm text-gray-900 whitespace-nowrap">
                          {row[col] !== null && row[col] !== undefined ? String(row[col]) : 'null'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {data.data.length === 0 && (
              <div className="text-center py-8 text-gray-500">Таблица пуста</div>
            )}
            {data.total > 0 && (
              <div className="px-4 py-3 bg-gray-50 border-t flex justify-end gap-2">
                <button
                  onClick={handlePrevPage}
                  disabled={offset === 0}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded disabled:opacity-50"
                >
                  Назад
                </button>
                <button
                  onClick={handleNextPage}
                  disabled={offset + limit >= data.total}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded disabled:opacity-50"
                >
                  Вперёд
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default TableViewer;