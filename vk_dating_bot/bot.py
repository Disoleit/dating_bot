import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id

from database.databasework import Session
from database.models import Users, Candidates, Photos, Interactions
from vk_dating_bot.vk_tools import VKTools
from vk_dating_bot.keyboards import get_main_keyboard, get_settings_keyboard, get_search_keyboard, get_empty_keyboard
from config import GROUP_TOKEN, GROUP_ID, DEFAULT_AGE, DEFAULT_CITY, DEFAULT_CITY_TITLE
from database.crud import add_user, add_candidate_with_link, add_interaction, get_favorite_candidates

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

        print(f"🆕 Сообщение от {user_id}: '{text}'")

        # Инициализация состояния пользователя
        is_new_user = False
        if user_id not in self.user_states:
            is_new_user = True
            self.user_states[user_id] = {
                    'search_params': {
                            'city_id':    DEFAULT_CITY,
                            'city_title': DEFAULT_CITY_TITLE,
                            'age_from':   18,
                            'age_to':     99,
                            'sex':        2
                    },
                    'state':         None
            }

        current_state = self.user_states[user_id].get('state')

        # Для новых пользователей сначала показываем приветствие
        if is_new_user:
            print(f"👤 Новый пользователь {user_id}, отправляем приветствие")
            self.send_welcome(user_id)
            return
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
        elif current_state == 'waiting_manual_city':
            self.process_manual_city_input(user_id, text)
            return
        elif current_state == 'waiting_manual_age':
            self.process_manual_age_input(user_id, text)
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
        elif text == 'обновить город':
            self.request_manual_city_input(user_id)
        elif text == 'обновить возраст':
            self.request_manual_age_input(user_id)
        else:
            self.process_user_info(user_id, text)


    def send_welcome(self, user_id):
        print(f"👋 Приветствие для пользователя {user_id}")
        self.user_states[user_id]['state'] = None

        # Получаем информацию о пользователе
        user_info = self.vk_tools.get_user_info(user_id)

        # Если не удалось получить информацию (приватный профиль)
        if user_info is None:
            print(f"⚠️ Профиль пользователя {user_id} приватный или недоступен")
            self.send_message(
                    user_id,
                    "Ваш профиль частично закрыт. Пожалуйста, укажите недостающую информацию.",
                    keyboard=get_empty_keyboard()
            )

            # Сохраняем пользователя с минимальными данными
            default_info = {
                    'name':       f"Пользователь {user_id}",
                    'age':        DEFAULT_AGE,
                    'gender':     2,
                    'city_id':    DEFAULT_CITY,
                    'city_title': DEFAULT_CITY_TITLE
            }
            self.save_user(user_id, **default_info)

            # Устанавливаем параметры поиска по умолчанию
            self.user_states[user_id]['search_params'] = {
                    'city_id':    DEFAULT_CITY,
                    'city_title': DEFAULT_CITY_TITLE,
                    'age_from':   18,
                    'age_to':     99,
                    'sex':        2
            }

            # Предлагаем настроить параметры
            message = (
                    "🔍 Пожалуйста, настройте параметры поиска:\n\n"
                    "1. Чтобы установить город, отправьте 'Обновить город'\n"
                    "2. Чтобы установить возраст, отправьте 'Обновить возраст'\n\n"
                    "После настройки вы можете начать поиск!"
            )
            self.send_message(user_id, message, keyboard=get_main_keyboard())
            return

        # Сохраняем пользователя с реальными данными
        save_success = self.save_user(
                user_id,
                user_info.get('name', f"Пользователь {user_id}"),
                user_info.get('age', DEFAULT_AGE),
                user_info.get('sex', 2),
                user_info.get('city_id', DEFAULT_CITY),
                user_info.get('city_title', DEFAULT_CITY_TITLE)
        )

        if not save_success:
            print(f"🔥 Критическая ошибка: не удалось сохранить пользователя {user_id}")
            # Пытаемся сохранить минимальные данные
            self.save_user(user_id, f"Пользователь {user_id}", DEFAULT_AGE, 2, DEFAULT_CITY, DEFAULT_CITY_TITLE)

        # Обработка данных пользователя
        user_age = user_info.get('age') or DEFAULT_AGE
        age_note = "" if user_info.get('age') else " (не указан в профиле)"

        city_id = user_info.get('city_id') or DEFAULT_CITY
        city_title = user_info.get('city_title') or DEFAULT_CITY_TITLE
        city_note = "" if user_info.get('city_id') else " (не указан в профиле)"

        sex = user_info.get('sex') or 2
        sex_note = "" if user_info.get('sex') else " (не указан в профиле)"

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
        print(f"🔍 Начало поиска для пользователя {user_id}")
        params = self.user_states[user_id]['search_params']

        # Проверка и корректировка параметров
        age_from = int(params.get('age_from', 18))
        age_to = int(params.get('age_to', 99))

        if age_from < 18: age_from = 18
        if age_to < age_from: age_to = age_from + 5

        params['age_from'] = age_from
        params['age_to'] = age_to

        # Проверка города
        if 'city_id' not in params or not params['city_id']:
            params['city_id'] = DEFAULT_CITY
            params['city_title'] = DEFAULT_CITY_TITLE
            self.send_message(user_id, f"⚠️ Город не был указан. Используется город по умолчанию: {DEFAULT_CITY_TITLE}")

        self.send_message(user_id, "🔍 Ищу подходящих кандидатов...", keyboard=get_empty_keyboard())

        # Поиск кандидатов
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

    def request_manual_city_input(self, user_id):
        """Запрос ручного ввода города"""
        print(f"🌆 Запрос города у пользователя {user_id}")
        self.user_states[user_id]['state'] = 'waiting_manual_city'
        self.send_message(user_id, "Введите название вашего города:")

    def process_manual_city_input(self, user_id, city_name):
        """Обработка ручного ввода города"""
        print(f"🌆 Обработка города '{city_name}' от пользователя {user_id}")

        cities = self.vk_tools.find_city(city_name)

        if not cities:
            self.send_message(user_id, "Город не найден. Попробуйте ввести другое название:")
            return

        # Сохраняем первый найденный город
        city_title = list(cities.keys())[0]
        city_id = cities[city_title]

        # Обновляем информацию о пользователе в БД
        session = Session()
        try:
            user = session.query(Users).filter_by(vk_id=user_id).first()
            if user:
                user.city_id = city_id
                user.city_title = city_title
                session.commit()
                print(f"✅ Город пользователя {user_id} обновлен: {city_title}")
        except Exception as e:
            print(f"❌ Ошибка при обновлении города: {e}")
        finally:
            session.close()

        # Обновляем параметры поиска
        self.user_states[user_id]['search_params']['city_id'] = city_id
        self.user_states[user_id]['search_params']['city_title'] = city_title
        self.user_states[user_id]['state'] = None

        self.send_message(
                user_id,
                f"✅ Город успешно сохранен: {city_title}\nТеперь вы можете начать поиск!",
                keyboard=get_main_keyboard()
        )

    def request_manual_age_input(self, user_id):
        """Запрос ручного ввода возраста"""
        print(f"🎂 Запрос возраста у пользователя {user_id}")
        self.user_states[user_id]['state'] = 'waiting_manual_age'
        self.send_message(user_id, "Введите ваш возраст:")

    def process_manual_age_input(self, user_id, text):
        """Обработка ручного ввода возраста"""
        print(f"🎂 Обработка возраста '{text}' от пользователя {user_id}")
        try:
            age = int(text)
            if age < 18 or age > 99:
                self.send_message(user_id, "Возраст должен быть от 18 до 99 лет. Попробуйте еще раз:")
                return
        except ValueError:
            self.send_message(user_id, "Пожалуйста, введите число от 18 до 99:")
            return

        # Обновляем информацию о пользователе в БД
        session = Session()
        try:
            user = session.query(Users).filter_by(vk_id=user_id).first()
            if user:
                user.age = age
                session.commit()
                print(f"✅ Возраст пользователя {user_id} обновлен: {age}")
        except Exception as e:
            print(f"❌ Ошибка при обновлении возраста: {e}")
        finally:
            session.close()

        # Обновляем параметры поиска
        params = self.user_states[user_id]['search_params']
        params['age_from'] = max(18, age - 5)
        params['age_to'] = min(99, age + 5)
        self.user_states[user_id]['state'] = None

        self.send_message(
                user_id,
                f"✅ Возраст успешно сохранен: {age} лет\nТеперь вы можете начать поиск!",
                keyboard=get_main_keyboard()
        )

    def process_city_selection(self, user_id, text):
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
                self.user_states[user_id]['search_params']['city_id'] = city_id
                self.user_states[user_id]['search_params']['city_title'] = city_name
                self.user_states[user_id]['state'] = None
                message = f"✅ Город успешно изменен на: {city_name}\n\nТеперь вы можете начать поиск!"
                self.send_message(user_id, message, keyboard=get_settings_keyboard())
            else:
                self.send_message(user_id, f"Пожалуйста, введите число от 1 до {len(cities)}:",
                                  keyboard=get_empty_keyboard())
        except ValueError:
            self.send_message(user_id, "Пожалуйста, введите номер города из списка:", keyboard=get_empty_keyboard())

    def stop_search(self, user_id):
        self.send_message(user_id, "Поиск остановлен. Вы можете начать новый поиск в любое время!",
                          keyboard=get_main_keyboard())

    def show_settings(self, user_id):
        params = self.user_states[user_id]['search_params']
        message = (
                f"⚙️ Текущие настройки:\n"
                f"• Город: {params.get('city_title', 'не указан')}\n"
                f"• Возрастной диапазон: от {params.get('age_from', 18)} до {params.get('age_to', 99)} лет\n\n"
                "Выберите параметр для изменения:"
        )
        self.send_message(user_id, message, keyboard=get_settings_keyboard())

    def request_city_input(self, user_id):
        self.user_states[user_id]['state'] = 'waiting_city'
        self.send_message(user_id, "Введите название города (например: Москва):", keyboard=get_empty_keyboard())

    def process_city_input(self, user_id, city_name):
        if len(city_name) < 2:
            self.send_message(user_id, "Название города слишком короткое. Попробуйте еще раз.")
            return

        cities = self.vk_tools.find_city(city_name)
        if not cities:
            self.send_message(user_id, "Город не найден. Попробуйте ввести другое название:")
            return

        self.city_cache[user_id] = cities
        message = "Найдены следующие города:\n" + "\n".join(
                [f"{i + 1}. {city}" for i, city in enumerate(cities.keys())]
        )
        message += "\n\nВведите номер выбранного города:"
        self.send_message(user_id, message, keyboard=get_empty_keyboard())
        self.user_states[user_id]['state'] = 'waiting_city_select'

    def request_age_range(self, user_id):
        params = self.user_states[user_id]['search_params']
        message = (
                f"Текущий возрастной диапазон: от {params.get('age_from', 18)} до {params.get('age_to', 99)} лет\n\n"
                "Введите минимальный возраст (от 18 лет):"
        )
        self.send_message(user_id, message, keyboard=get_empty_keyboard())
        self.user_states[user_id]['state'] = 'waiting_age_from'

    def process_age_input(self, user_id, text, age_type):
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
            message = f"✅ Возрастной диапазон обновлен: от {params['age_from']} до {params['age_to']} лет\n\nТеперь вы можете начать поиск!"
            self.send_message(user_id, message, keyboard=get_settings_keyboard())

    def send_next_candidate(self, user_id):
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

        # Сохраняем кандидата в БД
        photos_data = {
                'first_photo':  photos[0] if len(photos) > 0 else None,
                'second_photo': photos[1] if len(photos) > 1 else None,
                'third_photo':  photos[2] if len(photos) > 2 else None,
                'account_link': candidate['profile_link']
        }
        self.save_candidate(user_id, candidate['id'], candidate['name'],
                            None, None, None, None, photos_data)

        message = f"👤 {candidate['name']}\n🔗 Ссылка: {candidate['profile_link']}\n📸 Топ-3 фотографии:"
        self.send_message(user_id, message, attachment=",".join(photos), keyboard=get_search_keyboard())

    def add_to_favorites(self, user_id):
        if user_id not in self.favorites:
            self.favorites[user_id] = []

        candidate = self.user_states[user_id].get('current_candidate')
        if not candidate:
            self.send_message(user_id, "Сначала найдите кандидата!")
            return

        if candidate not in self.favorites[user_id]:
            self.favorites[user_id].append(candidate)
            # Сохраняем взаимодействие с статусом 'favorite'
            self.save_interaction(user_id, candidate['id'], 'favorite')
            self.send_message(user_id, "✅ Добавлено в избранное!", keyboard=get_search_keyboard())
        else:
            self.send_message(user_id, "❌ Уже в избранном!", keyboard=get_search_keyboard())

    def show_favorites(self, user_id):
        session = Session()
        try:
            # Получаем избранных кандидатов с фотографиями
            favorites = get_favorite_candidates(session, user_id)

            if not favorites:
                self.send_message(user_id, "У вас пока нет избранных кандидатов.")
                return

            # Отправляем сообщение с количеством избранных
            self.send_message(
                    user_id,
                    f"⭐ У вас {len(favorites)} избранных кандидатов:",
                    keyboard=get_main_keyboard()
            )

            time.sleep(0.5)  # Пауза перед отправкой фотографий

            # Отправляем каждого кандидата
            for i, candidate in enumerate(favorites, 1):
                photos = []
                if candidate.first_photo: photos.append(candidate.first_photo)
                if candidate.second_photo: photos.append(candidate.second_photo)
                if candidate.third_photo: photos.append(candidate.third_photo)

                message = (
                        f"⭐ Избранный кандидат #{i}:\n"
                        f"👤 Имя: {candidate.name}\n"
                        f"🔗 Ссылка: https://vk.com/id{candidate.vk_id}"
                )

                self.send_message(
                        user_id,
                        message,
                        attachment=",".join(photos) if photos else None
                )
                time.sleep(0.5)

        except Exception as e:
            print(f"Ошибка при получении избранных: {e}")
            self.send_message(user_id, "Произошла ошибка при получении избранных кандидатов.")
        finally:
            session.close()

    def send_help(self, user_id):
        message = (
                "🤖 Помощь по боту:\n"
                "• 'Поиск' - начать поиск по текущим настройкам\n"
                "• 'Настройки' - изменить город и возрастной диапазон\n"
                "• 'Следующий' - показать следующего кандидата\n"
                "• 'В избранное' - сохранить текущего кандидата\n"
                "• 'Стоп поиск' - завершить текущий поиск\n"
                "• 'Избранное' - показать сохраненных кандидатов\n"
                "• 'Обновить город' - установить ваш город\n"
                "• 'Обновить возраст' - установить ваш возраст\n"
                "• 'Помощь' - показать это сообщение\n\n"
                "Бот ищет людей по вашему городу и указанному возрастному диапазону"
        )
        self.send_message(user_id, message)

    def process_user_info(self, user_id, text):
        self.send_message(user_id, "Используйте кнопки для управления ботом 🤖")

    def send_message(self, user_id, message, keyboard=None, attachment=None):
        params = {
                'user_id':   user_id,
                'message':   message,
                'random_id': get_random_id(),
                'keyboard':  keyboard or get_main_keyboard()
        }
        if attachment:
            params['attachment'] = attachment

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

    def save_user(self, user_id, name, age, gender, city_id, city_title):
        session = Session()
        try:
            # Проверяем, не сохранен ли уже пользователь
            existing_user = session.query(Users).filter_by(vk_id=user_id).first()
            if existing_user:
                print(f"ℹ️ Пользователь {user_id} уже существует в БД")
                return True
            # Преобразуем пол в строковое значение
            gender_str = "unknown"
            if gender:
                gender_str = "female" if gender == 1 else "male"

            # Обеспечиваем значения по умолчанию
            name = name or f"Пользователь {user_id}"
            age = age or DEFAULT_AGE
            city_id = city_id or DEFAULT_CITY
            city_title = city_title or DEFAULT_CITY_TITLE

            # Сохраняем пользователя
            user = add_user(
                    session=session,
                    vk_id=user_id,
                    name=name,
                    age=age,
                    gender=gender_str,
                    city_id=city_id,
                    city_title=city_title
            )

            session.commit()
            print(f"✅ Пользователь {user_id} успешно сохранён в БД")
            return True
        except Exception as e:
            session.rollback()
            print(f"❌ Ошибка при сохранении пользователя {user_id}: {e}")
            return False
        finally:
            session.close()

    def save_candidate(self, user_id, candidate_id, name, age, gender, city_id, city_title, photos_data):
        session = Session()
        try:
            add_candidate_with_link(
                    session,
                    user_vk_id=user_id,
                    candidate_vk_id=candidate_id,
                    name=name,
                    age=age,
                    gender=gender,
                    city_id=city_id,
                    city_title=city_title,
                    photos_data=photos_data
            )
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Ошибка при сохранении кандидата: {e}")
            return False
        finally:
            session.close()

    def save_interaction(self, user_id, candidate_id, status):
        session = Session()
        try:
            add_interaction(
                    session,
                    user_vk_id=user_id,
                    candidate_vk_id=candidate_id,
                    status=status
            )
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Ошибка при сохранении взаимодействия: {e}")
            return False
        finally:
            session.close()

    def send_next_candidate(self, user_id):
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

        # Сохраняем кандидата в БД с ВСЕМИ данными
        photos_data = {
                'first_photo':  photos[0] if len(photos) > 0 else None,
                'second_photo': photos[1] if len(photos) > 1 else None,
                'third_photo':  photos[2] if len(photos) > 2 else None,
                'account_link': candidate['profile_link']
        }

        self.save_candidate(
                user_id,
                candidate['id'],
                candidate['name'],
                candidate['age'],  # Возраст
                candidate['gender'],  # Пол
                candidate['city_id'],  # ID города
                candidate['city_title'],  # Название города
                photos_data
        )

        message = f"👤 {candidate['name']}\n🔗 Ссылка: {candidate['profile_link']}\n📸 Топ-3 фотографии:"
        self.send_message(user_id, message, attachment=",".join(photos), keyboard=get_search_keyboard())