// frontend/src/pages/QuizPage.tsx
// Страница прохождения квиза
// Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

interface QuestionForUser {
  id: number;
  text: string;
  type: string; // 'single' в MVP
  options: string[];
}

interface QuizResult {
  quiz_id: number;
  correct_count: number;
  total_count: number;
  xp_earned: number;
}

const QuizPage: React.FC = () => {
  const { quizId } = useParams<{ quizId: string }>();
  const navigate = useNavigate();

  const [questions, setQuestions] = useState<QuestionForUser[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchQuestions();
  }, [quizId]);

  const fetchQuestions = async () => {
    if (!quizId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.get(`/api/learn/quiz/${quizId}`);
      setQuestions(response.data);
      // Инициализируем массив ответов пустыми значениями (null или -1)
      setAnswers(new Array(response.data.length).fill(-1));
    } catch (err) {
      console.error('Failed to fetch quiz questions:', err);
      setError('Не удалось загрузить вопросы квиза. Попробуйте позже.');
    } finally {
      setLoading(false);
    }
  };

  const handleOptionChange = (optionIndex: number) => {
    setSelectedOption(optionIndex);
  };

  const handleNext = () => {
    if (selectedOption === null) return;

    // Сохраняем ответ для текущего вопроса
    const newAnswers = [...answers];
    newAnswers[currentIndex] = selectedOption;
    setAnswers(newAnswers);

    if (currentIndex < questions.length - 1) {
      // Переходим к следующему вопросу
      setCurrentIndex(currentIndex + 1);
      setSelectedOption(null);
    } else {
      // Это был последний вопрос, отправляем ответы
      submitQuiz(newAnswers);
    }
  };

  const submitQuiz = async (finalAnswers: number[]) => {
    if (!quizId) return;
    setSubmitting(true);
    setError(null);
    try {
      const response = await api.post('/api/learn/quiz/submit', {
        quiz_id: parseInt(quizId),
        answers: finalAnswers,
      });
      setResult(response.data);
    } catch (err) {
      console.error('Failed to submit quiz:', err);
      setError('Ошибка при отправке ответов. Попробуйте снова.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = () => {
    // Сброс состояния для повторного прохождения
    setCurrentIndex(0);
    setAnswers(new Array(questions.length).fill(-1));
    setSelectedOption(null);
    setResult(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Загрузка квиза...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-500 text-lg">{error}</div>
      </div>
    );
  }

  if (!questions.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Квиз не найден</h2>
        <Link to="/dashboard" className="text-indigo-600 hover:underline">
          Вернуться на главную
        </Link>
      </div>
    );
  }

  if (result) {
    // Показываем результат
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4">
        <div className="max-w-2xl mx-auto bg-white shadow-lg rounded-lg p-8">
          <h2 className="text-2xl font-bold text-center mb-6">Результат</h2>
          <div className="text-center mb-6">
            <p className="text-lg">
              Правильных ответов: <span className="font-bold">{result.correct_count}</span> из {result.total_count}
            </p>
            <p className="text-lg mt-2">
              Получено опыта: <span className="font-bold text-green-600">{result.xp_earned} XP</span>
            </p>
          </div>
          <div className="flex justify-center gap-4">
            <button
              onClick={handleRetry}
              className="px-6 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
            >
              Пройти заново
            </button>
            <Link
              to="/dashboard"
              className="px-6 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
            >
              На главную
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const currentQuestion = questions[currentIndex];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Прогресс */}
        <div className="mb-4 text-sm text-gray-500 text-right">
          Вопрос {currentIndex + 1} из {questions.length}
        </div>

        {/* Вопрос */}
        <div className="bg-white shadow-lg rounded-lg p-8 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">
            {currentQuestion.text}
          </h2>
          <div className="space-y-3">
            {currentQuestion.options.map((option, idx) => (
              <label key={idx} className="flex items-center space-x-3 p-3 border rounded hover:bg-gray-50 cursor-pointer">
                <input
                  type="radio"
                  name="quiz-option"
                  value={idx}
                  checked={selectedOption === idx}
                  onChange={() => handleOptionChange(idx)}
                  className="h-4 w-4 text-indigo-600"
                />
                <span className="text-gray-800">{option}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Кнопка Далее */}
        <button
          onClick={handleNext}
          disabled={selectedOption === null || submitting}
          className="w-full py-3 px-4 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition disabled:bg-indigo-300"
        >
          {currentIndex < questions.length - 1 ? 'Далее' : 'Завершить'}
        </button>

        {submitting && (
          <div className="mt-4 text-center text-gray-600">Отправка ответов...</div>
        )}
      </div>
    </div>
  );
};

export default QuizPage;