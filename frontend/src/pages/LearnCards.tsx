// frontend/src/pages/LearnCards.tsx
// Страница изучения карточек (интервальные повторения)
// Версия: соответствует ТЗ Dominiq-MVP-TZ-v1.0

import React, { useEffect, useState } from 'react';
import api from '../services/api';

interface Card {
  id: number;
  term: string;
  definition: string;
  example?: string | null;
  simplified_definition?: string | null;
  hint?: string | null;
}

const LearnCards: React.FC = () => {
  const [cards, setCards] = useState<Card[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [xpMessage, setXpMessage] = useState<string | null>(null);

  // Загружаем карточки при монтировании
  useEffect(() => {
    fetchDueCards();
  }, []);

  const fetchDueCards = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.get('/api/learn/cards/due?limit=20');
      setCards(response.data);
    } catch (err) {
      console.error('Failed to fetch due cards:', err);
      setError('Не удалось загрузить карточки. Попробуйте позже.');
    } finally {
      setLoading(false);
    }
  };

  const handleReveal = () => {
    setShowAnswer(true);
  };

  const handleReview = async (known: boolean) => {
    const cardId = cards[currentIndex].id;
    setXpMessage(null);
    try {
      const response = await api.post('/api/learn/cards/review', {
        card_id: cardId,
        known,
      });
      // Показываем сообщение о полученном опыте
      setXpMessage(`+${response.data.xp_earned} XP`);
      // Переходим к следующей карточке
      if (currentIndex < cards.length - 1) {
        setCurrentIndex(currentIndex + 1);
        setShowAnswer(false);
      } else {
        // Карточки закончились
        setCards([]);
        setCurrentIndex(0);
        setShowAnswer(false);
      }
    } catch (err) {
      console.error('Failed to submit review:', err);
      setError('Ошибка при отправке ответа');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Загрузка карточек...</div>
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

  if (cards.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Нет карточек для повторения</h2>
        <p className="text-gray-600 mb-8">Загляните позже или изучите новые темы.</p>
        <button
          onClick={fetchDueCards}
          className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          Обновить
        </button>
      </div>
    );
  }

  const currentCard = cards[currentIndex];

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Прогресс */}
        <div className="mb-4 text-sm text-gray-500 text-right">
          Карточка {currentIndex + 1} из {cards.length}
        </div>

        {/* Карточка */}
        <div className="bg-white shadow-lg rounded-lg p-8 mb-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-gray-900 mb-4">
              {currentCard.term}
            </div>
            {showAnswer && (
              <div className="mt-6 border-t pt-6">
                <div className="text-left mb-4">
                  <h3 className="text-lg font-semibold text-gray-700">Определение:</h3>
                  <p className="text-gray-800">
                    {currentCard.simplified_definition || currentCard.definition}
                  </p>
                </div>
                {currentCard.example && (
                  <div className="text-left mb-4">
                    <h3 className="text-lg font-semibold text-gray-700">Пример:</h3>
                    <p className="text-gray-600 italic">"{currentCard.example}"</p>
                  </div>
                )}
                {currentCard.hint && (
                  <div className="text-left">
                    <h3 className="text-lg font-semibold text-gray-700">Подсказка:</h3>
                    <p className="text-gray-600">{currentCard.hint}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Сообщение об опыте */}
        {xpMessage && (
          <div className="mb-4 text-center text-green-600 font-semibold animate-pulse">
            {xpMessage}
          </div>
        )}

        {/* Кнопки */}
        {!showAnswer ? (
          <button
            onClick={handleReveal}
            className="w-full py-3 px-4 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition"
          >
            Показать ответ
          </button>
        ) : (
          <div className="flex gap-4">
            <button
              onClick={() => handleReview(false)}
              className="flex-1 py-3 px-4 bg-red-500 text-white font-medium rounded-lg hover:bg-red-600 transition"
            >
              Не знаю
            </button>
            <button
              onClick={() => handleReview(true)}
              className="flex-1 py-3 px-4 bg-green-500 text-white font-medium rounded-lg hover:bg-green-600 transition"
            >
              Знаю
            </button>
          </div>
        )}

        {/* Кнопка сброса/обновления */}
        <div className="mt-6 text-center">
          <button
            onClick={fetchDueCards}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Обновить список карточек
          </button>
        </div>
      </div>
    </div>
  );
};

export default LearnCards;