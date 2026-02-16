// frontend/src/App.tsx
// Главный компонент с маршрутизацией и защитой маршрутов
// Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0 + планы развития

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import LearnCards from './pages/LearnCards';
import QuizzesList from './pages/QuizzesList';
import QuizPage from './pages/QuizPage';
import Achievements from './pages/Achievements';
import DocumentUpload from './pages/admin/DocumentUpload';
import DraftList from './pages/admin/DraftList';
import TermManager from './pages/admin/TermManager';
import PlanManager from './pages/admin/PlanManager'; // новый компонент для управления планами
import MyPlan from './pages/MyPlan';

// Компонент защищённого маршрута
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const userEmail = localStorage.getItem('userEmail');
  if (!userEmail) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="cards" element={<LearnCards />} />
          <Route path="quizzes" element={<QuizzesList />} />
          <Route path="quiz/:quizId" element={<QuizPage />} />
          <Route path="achievements" element={<Achievements />} />
          <Route path="my-plan" element={<MyPlan />} />
          {/* Админские маршруты */}
          <Route path="admin/upload" element={<DocumentUpload />} />
          <Route path="admin/drafts" element={<DraftList />} />
          <Route path="admin/terms" element={<TermManager />} />
          <Route path="admin/plans" element={<PlanManager />} /> {/* новый маршрут */}
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;