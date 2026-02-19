// frontend/src/components/Layout.tsx
// Общий макет с навигацией и выходом
// Добавлено подменю "Кабинет методиста" для административных ссылок

import React, { useState } from 'react';
import { Link, Outlet, useNavigate } from 'react-router-dom';

const Layout: React.FC = () => {
  const navigate = useNavigate();
  const userEmail = localStorage.getItem('userEmail');
  const [isMethodistMenuOpen, setIsMethodistMenuOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('userEmail');
    navigate('/login');
  };

  const toggleMethodistMenu = () => {
    setIsMethodistMenuOpen(!isMethodistMenuOpen);
  };

  const closeMethodistMenu = () => {
    setIsMethodistMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex">
              <Link to="/dashboard" className="flex items-center px-2 py-2 text-gray-700 hover:text-indigo-600">
                Dominiq
              </Link>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                {/* Основные пользовательские пункты */}
                <Link to="/cards" className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 hover:text-indigo-600">
                  Карточки
                </Link>
                <Link to="/quizzes" className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 hover:text-indigo-600">
                  Квизы
                </Link>
                <Link to="/my-plan" className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 hover:text-indigo-600">
                  Мой план
                </Link>
                <Link to="/achievements" className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 hover:text-indigo-600">
                  Достижения
                </Link>

                {/* Кабинет методиста (выпадающее меню) */}
                <div className="relative inline-flex items-center">
                  <button
                    onClick={toggleMethodistMenu}
                    className="inline-flex items-center px-1 pt-1 text-sm font-medium text-gray-900 hover:text-indigo-600 focus:outline-none"
                  >
                    Кабинет методиста
                    <svg
                      className={`ml-1 h-4 w-4 transition-transform ${isMethodistMenuOpen ? 'rotate-180' : ''}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {isMethodistMenuOpen && (
                    <div
                      className="absolute top-full left-0 mt-1 w-48 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 py-1 z-50"
                      onMouseLeave={closeMethodistMenu}
                    >
                      <Link
                        to="/admin/upload"
                        onClick={closeMethodistMenu}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-indigo-600"
                      >
                        Загрузить документ
                      </Link>
                      <Link
                        to="/admin/drafts"
                        onClick={closeMethodistMenu}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-indigo-600"
                      >
                        Черновики
                      </Link>
                      <Link
                        to="/admin/terms"
                        onClick={closeMethodistMenu}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-indigo-600"
                      >
                        Термины
                      </Link>
                      <Link
                        to="/admin/plans"
                        onClick={closeMethodistMenu}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-indigo-600"
                      >
                        Планы развития
                      </Link>
                      {/* Новая ссылка на подбор тем */}
                      <Link
                        to="/admin/topics"
                        onClick={closeMethodistMenu}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-indigo-600"
                      >
                        Подбор тем
                      </Link>  
                      {/* Ссылка на сохранённые сессии */}
                      <Link
                        to="/admin/saved-topics"
                        onClick={closeMethodistMenu}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-indigo-600"
                      >
                        Сохранённые сессии
                      </Link>  
                      <Link
                        to="/admin/table-viewer"
                        onClick={closeMethodistMenu}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-indigo-600"
                      >
                      Просмотр БД
                      </Link>                 
                      <Link
                        to="admin/reset"
                        onClick={closeMethodistMenu}
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-indigo-600"
                      >
                        Управление БД
                      </Link>
                    </div>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-500">{userEmail}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Выйти
              </button>
            </div>
          </div>
        </div>
      </nav>
      <main>
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;