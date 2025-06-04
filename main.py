import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_dating_bot.vk_tools import VKTools
from vk_dating_bot.keyboards import get_main_keyboard, get_settings_keyboard, get_search_keyboard, get_empty_keyboard
from config import GROUP_TOKEN, GROUP_ID, DEFAULT_AGE, DEFAULT_CITY, DEFAULT_CITY_TITLE
import time


class DatingBot:

    def __init__(self):
        self.vk_tools = VKTools()
        self.vk_session = vk_api.VkApi(token=GROUP_TOKEN)
        self.longpoll = VkBotLongPoll(self.vk_session, GROUP_ID)
        self.vk = self.vk_session.get_api()
        self.user_states = {}
        self.search_results = {}
        self.favorites = {}
        self.city_cache = {}

    def start(self):
        print("Бот запущен...")
        for event in self.longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                self.handle_message(event)

    def handle_message(self, event):
        user_id = event.obj.message['from_id']
        text = event.obj.message['text'].lower()

        if user_id not in self.user_states:
            self.user_states[user_id] = {
                    'search_params': {
                            'city_id':    DEFAULT_CITY,
                            'city_title': DEFAULT_CITY_TITLE,
                            'age_from':   18,
                            'age_to':     99,
                            'sex':        2  # Пол по умолчанию
                    },
                    'state':         None
            }

        current_state = self.user_states[user_id].get('state')

        # Обработка состояний ввода
        if current_state == 'waiting_city':
            self.process_city_input(user_id, text)
            return
        elif current_state == 'waiting_city_select':
            self.process_city_selection(user_id, text)
            return
        elif current_state == 'waiting_age_from':
            self.process_age_input(user_id, text, 'from')
            return
        elif current_state == 'waiting_age_to':
            self.process_age_input(user_id, text, 'to')
            return

        # Обработка команд
        if text in ['привет', 'начать', 'старт']:
            self.send_welcome(user_id)
        elif text == 'поиск':
            self.start_search(user_id)
        elif text == 'настройки':
            self.show_settings(user_id)
        elif text == 'изменить город':
            self.request_city_input(user_id)
        elif text == 'изменить возраст':
            self.request_age_range(user_id)
        elif text == 'назад':
            self.send_welcome(user_id)
        elif text == 'следующий':
            self.send_next_candidate(user_id)
        elif text == 'в избранное':
            self.add_to_favorites(user_id)
        elif text == 'стоп поиск':
            self.stop_search(user_id)
        elif text == 'избранное':
            self.show_favorites(user_id)
        elif text == 'помощь':
            self.send_help(user_id)
        else:
            self.process_user_info(user_id, text)

    def process_city_selection(self, user_id, text):
        """Обработка выбора города из списка"""
        if user_id not in self.city_cache or not self.city_cache[user_id]:
            self.send_message(user_id, "Ошибка: список городов недоступен. Попробуйте еще раз.")
            self.request_city_input(user_id)
            return

        cities = list(self.city_cache[user_id].keys())

        try:
            choice = int(text)
            if 1 <= choice <= len(cities):
                city_name = cities[choice - 1]
                city_id = self.city_cache[user_id][city_name]

                # Обновляем параметры поиска
                self.user_states[user_id]['search_params']['city_id'] = city_id
                self.user_states[user_id]['search_params']['city_title'] = city_name
                self.user_states[user_id]['state'] = None

                message = (
                        f"✅ Город успешно изменен на: {city_name}\n\n"
                        "Теперь вы можете начать поиск!"
                )

                self.send_message(
                        user_id,
                        message,
                        keyboard=get_settings_keyboard()
                )
            else:
                self.send_message(
                        user_id,
                        f"Пожалуйста, введите число от 1 до {len(cities)}:",
                        keyboard=get_empty_keyboard()
                )
        except ValueError:
            self.send_message(
                    user_id,
                    "Пожалуйста, введите номер города из списка:",
                    keyboard=get_empty_keyboard()
            )

    def send_welcome(self, user_id):
        """Приветственное сообщение"""
        self.user_states[user_id]['state'] = None

        # Получение информации о пользователе
        user_info = self.vk_tools.get_user_info(user_id)
        if not user_info:
            self.send_message(user_id, "Не удалось получить ваши данные. Проверьте настройки приватности.")
            return

        # Обработка возраста
        user_age = user_info.get('age')
        if user_age is None:
            user_age = DEFAULT_AGE
            age_note = " (не указан в профиле)"
        else:
            age_note = ""

        # Обработка города
        city_id = user_info.get('city_id')
        city_title = user_info.get('city_title')
        if not city_id or not city_title:
            city_id = DEFAULT_CITY
            city_title = DEFAULT_CITY_TITLE
            city_note = " (не указан в профиле)"
        else:
            city_note = ""

        # Обработка пола
        sex = user_info.get('sex')
        if sex is None:
            sex = 2
            sex_note = " (не указан в профиле)"
        else:
            sex_note = ""

        # Инициализация параметров поиска
        params = {
                'age':        user_age,
                'sex':        sex,
                'city_id':    city_id,
                'city_title': city_title,
                'age_from':   max(18, user_age - 5),
                'age_to':     min(99, user_age + 5)
        }

        # Сохранение параметров
        self.user_states[user_id]['search_params'] = params

        message = (
                f"Привет, {user_info['name']}!\n"
                f"Я помогу тебе найти новых друзей 😊\n\n"
                f"🔍 Текущие настройки поиска:\n"
                f"• Город: {city_title}{city_note}\n"
                f"• Возраст: {user_age}{age_note}\n"
                f"• Пол: {'Мужской' if sex == 2 else 'Женский'}{sex_note}\n"
                f"• Возрастной диапазон: от {params['age_from']} до {params['age_to']} лет\n\n"
                "Нажми 'Поиск' чтобы начать или 'Настройки' чтобы изменить параметры!"
        )
        self.send_message(user_id, message, keyboard=get_main_keyboard())

    def start_search(self, user_id):
        """Начало поиска"""
        params = self.user_states[user_id]['search_params']

        # Проверка и установка пола по умолчанию
        if 'sex' not in params or not params['sex']:
            params['sex'] = 2

        # Гарантируем корректные значения возраста
        age_from = int(params.get('age_from', 18))
        age_to = int(params.get('age_to', 99))

        if not isinstance(age_from, int) or age_from < 18:
            age_from = 18
        if not isinstance(age_to, int) or age_to < age_from:
            age_to = age_from + 5

        # Обновляем параметры
        params['age_from'] = age_from
        params['age_to'] = age_to

        # Сброс предыдущих результатов
        if user_id in self.search_results:
            del self.search_results[user_id]

        # Проверка города
        if 'city_id' not in params or not params['city_id']:
            params['city_id'] = DEFAULT_CITY
            params['city_title'] = DEFAULT_CITY_TITLE
            self.send_message(
                    user_id,
                    f"⚠️ Город не был указан. Используется город по умолчанию: {DEFAULT_CITY_TITLE}"
            )

        self.send_message(user_id, "🔍 Ищу подходящих кандидатов...", keyboard=get_empty_keyboard())

        candidates = self.vk_tools.search_users({
                'city_id':  params['city_id'],
                'age_from': params['age_from'],
                'age_to':   params['age_to'],
                'sex':      params['sex']
        }, count=50)

        if not candidates:
            self.send_message(user_id, "К сожалению, подходящих кандидатов не найдено 😔", keyboard=get_main_keyboard())
            return

        self.search_results[user_id] = candidates
        self.user_states[user_id]['current_index'] = 0

        message = (
                f"✅ Найдено кандидатов: {len(candidates)}\n"
                f"Город: {params['city_title']}\n"
                f"Возраст: от {params['age_from']} до {params['age_to']} лет\n\n"
                "Нажмите 'Следующий' чтобы увидеть первого кандидата!"
        )
        self.send_message(user_id, message, keyboard=get_search_keyboard())

    def stop_search(self, user_id):
        """Остановка поиска"""
        self.send_message(user_id, "Поиск остановлен. Вы можете начать новый поиск в любое время!",
                          keyboard=get_main_keyboard())

    def show_settings(self, user_id):
        """Показ настроек"""
        params = self.user_states[user_id]['search_params']
        message = (
                f"⚙️ Текущие настройки:\n"
                f"• Город: {params.get('city_title', 'не указан')}\n"
                f"• Возрастной диапазон: от {params.get('age_from', 18)} до {params.get('age_to', 99)} лет\n\n"
                "Выберите параметр для изменения:"
        )
        self.send_message(user_id, message, keyboard=get_settings_keyboard())

    def request_city_input(self, user_id):
        """Запрос ввода города"""
        self.user_states[user_id]['state'] = 'waiting_city'
        self.send_message(user_id, "Введите название города (например: Москва):", keyboard=get_empty_keyboard())

    def process_city_input(self, user_id, city_name):
        """Обработка введенного города"""
        if len(city_name) < 2:
            self.send_message(user_id, "Название города слишком короткое. Попробуйте еще раз.")
            return

        # Поиск города
        cities = self.vk_tools.find_city(city_name)

        if not cities:
            self.send_message(user_id, "Город не найден. Попробуйте ввести другое название:")
            return

        # Сохраняем кэш городов
        self.city_cache[user_id] = cities

        # Формируем сообщение с вариантами
        message = "Найдены следующие города:\n" + "\n".join(
                [f"{i + 1}. {city}" for i, city in enumerate(cities.keys())]
        )
        message += "\n\nВведите номер выбранного города:"

        self.send_message(user_id, message, keyboard=get_empty_keyboard())
        self.user_states[user_id]['state'] = 'waiting_city_select'

    def request_age_range(self, user_id):
        """Запрос возрастного диапазона"""
        params = self.user_states[user_id]['search_params']
        message = (
                f"Текущий возрастной диапазон: от {params.get('age_from', 18)} до {params.get('age_to', 99)} лет\n\n"
                "Введите минимальный возраст (от 18 лет):"
        )
        self.send_message(user_id, message, keyboard=get_empty_keyboard())
        self.user_states[user_id]['state'] = 'waiting_age_from'

    def process_age_input(self, user_id, text, age_type):
        """Обработка введенного возраста"""
        try:
            age = int(text)
            if age < 18 or age > 99:
                self.send_message(user_id, "Возраст должен быть от 18 до 99 лет. Попробуйте еще раз:")
                return
        except ValueError:
            self.send_message(user_id, "Пожалуйста, введите число от 18 до 99:")
            return

        params = self.user_states[user_id]['search_params']

        if age_type == 'from':
            params['age_from'] = age
            self.user_states[user_id]['state'] = 'waiting_age_to'
            self.send_message(user_id, "Теперь введите максимальный возраст:")
        else:
            if age < params.get('age_from', 18):
                self.send_message(user_id,
                                  "Максимальный возраст не может быть меньше минимального. Попробуйте еще раз:")
                return

            params['age_to'] = age
            self.user_states[user_id]['state'] = None

            message = (
                    f"✅ Возрастной диапазон обновлен: от {params['age_from']} до {params['age_to']} лет\n\n"
                    "Теперь вы можете начать поиск!"
            )

            self.send_message(user_id, message, keyboard=get_settings_keyboard())

    def send_next_candidate(self, user_id):
        """Отправка следующего кандидата"""
        if user_id not in self.search_results or not self.search_results[user_id]:
            self.send_message(user_id, "Сначала начните поиск командой 'Поиск'!")
            return

        idx = self.user_states[user_id].get('current_index', 0)
        if idx >= len(self.search_results[user_id]):
            self.send_message(user_id, "Все кандидаты просмотрены! Начните новый поиск.")
            return

        candidate = self.search_results[user_id][idx]
        self.user_states[user_id]['current_index'] = idx + 1
        self.user_states[user_id]['current_candidate'] = candidate

        photos = self.vk_tools.get_top_photos(candidate['id'])

        message = (
                f"👤 {candidate['name']}\n"
                f"🔗 Ссылка: {candidate['profile_link']}\n"
                "📸 Топ-3 фотографии:"
        )

        self.send_message(user_id, message, attachment=",".join(photos), keyboard=get_search_keyboard())

    def add_to_favorites(self, user_id):
        """Добавление в избранное"""
        if user_id not in self.favorites:
            self.favorites[user_id] = []

        candidate = self.user_states[user_id].get('current_candidate')
        if not candidate:
            self.send_message(user_id, "Сначала найдите кандидата!")
            return

        if candidate not in self.favorites[user_id]:
            self.favorites[user_id].append(candidate)
            self.send_message(user_id, "✅ Добавлено в избранное!", keyboard=get_search_keyboard())
        else:
            self.send_message(user_id, "❌ Уже в избранном!", keyboard=get_search_keyboard())

    def show_favorites(self, user_id):
        """Показ избранных кандидатов"""
        if user_id not in self.favorites or not self.favorites[user_id]:
            self.send_message(user_id, "У вас пока нет избранных кандидатов.")
            return

        message = "⭐ Ваши избранные кандидаты:\n\n"
        for i, candidate in enumerate(self.favorites[user_id], 1):
            message += f"{i}. {candidate['name']} - {candidate['profile_link']}\n"

        self.send_message(user_id, message)

    def send_help(self, user_id):
        """Отправка справки"""
        message = (
                "🤖 Помощь по боту:\n"
                "• 'Поиск' - начать поиск по текущим настройкам\n"
                "• 'Настройки' - изменить город и возрастной диапазон\n"
                "• 'Следующий' - показать следующего кандидата\n"
                "• 'В избранное' - сохранить текущего кандидата\n"
                "• 'Стоп поиск' - завершить текущий поиск\n"
                "• 'Избранное' - показать сохраненных кандидатов\n"
                "• 'Помощь' - показать это сообщение\n\n"
                "Бот ищет людей по вашему городу и указанному возрастному диапазону"
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
                'keyboard':  keyboard
        }
        if attachment:
            params['attachment'] = attachment

        if params['keyboard'] is None:
            params['keyboard'] = get_main_keyboard()

        for attempt in range(3):
            try:
                self.vk.messages.send(**params)
                break
            except vk_api.exceptions.ApiError as e:
                if e.code == 6:  # Too many requests
                    time.sleep(0.5)
                else:
                    print(f"Ошибка отправки сообщения: {e}")
                    break


if __name__ == "__main__":
    bot = DatingBot()
    bot.start()