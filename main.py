import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_tools import VKTools
from keyboards import get_main_keyboard, get_empty_keyboard
from config import GROUP_TOKEN, GROUP_ID, DEFAULT_AGE, DEFAULT_CITY
import time


class DatingBot:

    def __init__(self):
        # Инициализация инструментов VK с USER_TOKEN
        self.vk_tools = VKTools()

        # Инициализация бота с GROUP_TOKEN
        self.vk_session = vk_api.VkApi(token=GROUP_TOKEN)
        self.longpoll = VkBotLongPoll(self.vk_session, GROUP_ID)
        self.vk = self.vk_session.get_api()

        # Временное хранилище (заменится на БД)
        self.user_states = {}
        self.search_results = {}
        self.favorites = {}

    def start(self):
        """Запуск бота"""
        print("Бот запущен...")
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.handle_message(event)

    def handle_message(self, event):
        """Обработка входящих сообщений"""
        user_id = event.obj.message['from_id']
        text = event.obj.message['text'].lower()

        # Инициализация состояния пользователя
        if user_id not in self.user_states:
            self.user_states[user_id] = {'search_params': {}}

        # Обработка команд
        if text in ['привет', 'начать', 'старт']:
            self.send_welcome(user_id)
        elif text == 'следующий':
            self.send_next_candidate(user_id)
        elif text == 'в избранное':
            self.add_to_favorites(user_id)
        elif text == 'избранное':
            self.show_favorites(user_id)
        elif text == 'помощь':
            self.send_help(user_id)
        else:
            self.process_user_info(user_id, text)

    def send_welcome(self, user_id):
        """Приветственное сообщение"""
        user_info = self.vk_tools.get_user_info(user_id)
        if not user_info:
            self.send_message(user_id, "Не удалось получить ваши данные. Проверьте настройки приватности.")
            return

        # Сохраняем информацию для поиска
        self.user_states[user_id]['search_params'] = {
                'age':        user_info.get('age', DEFAULT_AGE),
                'sex':        user_info.get('sex'),
                'city_id':    user_info.get('city_id', DEFAULT_CITY),
                'city_title': user_info.get('city_title', 'Москва')
        }

        message = (
                f"Привет, {user_info['name']}!\n"
                f"Я помогу тебе найти новых друзей 😊\n"
                f"Твои данные для поиска:\n"
                f"• Город: {self.user_states[user_id]['search_params']['city_title']}\n"
                f"• Возраст: {self.user_states[user_id]['search_params']['age']}\n\n"
                "Нажми 'Следующий' чтобы начать поиск!"
        )
        self.send_message(user_id, message, keyboard=get_main_keyboard())

    def send_next_candidate(self, user_id):
        """Отправка следующего кандидата"""
        # Проверка и инициализация результатов поиска
        if user_id not in self.search_results or not self.search_results[user_id]:
            params = self.user_states[user_id]['search_params']
            candidates = self.vk_tools.search_users(params, count=50)
            self.search_results[user_id] = candidates
            self.user_states[user_id]['current_index'] = 0

            if not candidates:
                self.send_message(user_id, "К сожалению, подходящих кандидатов не найдено 😔")
                return

        # Получение текущего кандидата
        idx = self.user_states[user_id].get('current_index', 0)
        if idx >= len(self.search_results[user_id]):
            self.send_message(user_id, "Все кандидаты просмотрены! Начните новый поиск.")
            return

        candidate = self.search_results[user_id][idx]
        self.user_states[user_id]['current_index'] = idx + 1
        self.user_states[user_id]['current_candidate'] = candidate

        # Получение фотографий
        photos = self.vk_tools.get_top_photos(candidate['id'])

        # Формирование сообщения
        message = (
                f"{candidate['name']}\n"
                f"Ссылка: {candidate['profile_link']}\n"
                "Топ-3 фотографии:"
        )

        # Отправка сообщения с фотографиями
        self.send_message(user_id, message, attachment=",".join(photos))

    def add_to_favorites(self, user_id):
        """Добавление в избранное (временное хранилище)"""
        if user_id not in self.favorites:
            self.favorites[user_id] = []

        candidate = self.user_states[user_id].get('current_candidate')
        if not candidate:
            self.send_message(user_id, "Сначала найдите кандидата!")
            return

        if candidate not in self.favorites[user_id]:
            self.favorites[user_id].append(candidate)
            self.send_message(user_id, "✅ Добавлено в избранное!")
        else:
            self.send_message(user_id, "❌ Уже в избранном!")

    def show_favorites(self, user_id):
        """Показ избранных кандидатов"""
        if user_id not in self.favorites or not self.favorites[user_id]:
            self.send_message(user_id, "У вас пока нет избранных кандидатов.")
            return

        message = "Ваши избранные кандидаты:\n\n"
        for i, candidate in enumerate(self.favorites[user_id], 1):
            message += f"{i}. {candidate['name']} - {candidate['profile_link']}\n"

        self.send_message(user_id, message)

    def send_help(self, user_id):
        """Отправка справки"""
        message = (
                "🤖 Помощь по боту:\n"
                "• 'Следующий' - показать следующего кандидата\n"
                "• 'В избранное' - сохранить текущего кандидата\n"
                "• 'Избранное' - показать сохраненных кандидатов\n"
                "• 'Помощь' - показать это сообщение\n\n"
                "Бот ищет людей по вашему городу и возрасту (±5 лет)"
        )
        self.send_message(user_id, message)

    def process_user_info(self, user_id, text):
        """Обработка произвольного текста"""
        self.send_message(user_id, "Используйте кнопки для управления ботом 🤖")

    def send_message(self, user_id, message, keyboard=None, attachment=None):
        """Отправка сообщения"""
        params = {
                'user_id':   user_id,
                'message':   message,
                'random_id': get_random_id(),
                'keyboard':  keyboard or get_main_keyboard()
        }
        if attachment:
            params['attachment'] = attachment

        # Повторная попытка при ошибке "Too many requests"
        for attempt in range(3):
            try:
                self.vk.messages.send(**params)
                break
            except vk_api.exceptions.ApiError as e:
                if e.code == 6:  # Too many requests
                    time.sleep(0.5)  # Задержка перед повторной попыткой
                else:
                    print(f"Ошибка отправки сообщения: {e}")
                    break


if __name__ == "__main__":
    bot = DatingBot()
    bot.start()