import vk_api
from vk_api.exceptions import ApiError
from datetime import datetime
from config import USER_TOKEN, API_VERSION
import time

class VKTools:
    def __init__(self):
        self.user_vk = vk_api.VkApi(token=USER_TOKEN, api_version=API_VERSION)
        self.api = self.user_vk.get_api()
        self.api_version = API_VERSION

    def get_user_info(self, user_id: int) -> dict:
        try:
            print(f"[VK] Запрос информации о пользователе {user_id}...")
            response = self.api.users.get(
                    user_ids=user_id,
                    fields='sex,bdate,city,home_town,relation'  # Добавлено home_town
            )

            if not response:
                print(f"[VK] ❌ Пустой ответ для пользователя {user_id}")
                return None  # Возвращаем None вместо пустого словаря

            user = response[0]
            print(f"[VK] Получены данные: {user}")

            # Обработка города (пробуем разные варианты)
            city_id = None
            city_title = None

            # Вариант 1: из поля 'city'
            if 'city' in user:
                city_id = user['city']['id']
                city_title = user['city']['title']

            # Вариант 2: из поля 'home_town'
            elif 'home_town' in user and user['home_town']:
                # Пробуем найти город по названию
                cities = self.find_city(user['home_town'])
                if cities:
                    city_title = list(cities.keys())[0]
                    city_id = cities[city_title]

            # Обработка возраста
            age = self.calculate_age(user.get('bdate'))

            # Обработка имени
            first_name = user.get('first_name', '')
            last_name = user.get('last_name', '')
            name = f"{first_name} {last_name}".strip()
            if not name:
                name = f"Пользователь {user_id}"

            return {
                    'id':         user['id'],
                    'name':       name,
                    'sex':        user.get('sex'),
                    'age':        age,
                    'city_id':    city_id,
                    'city_title': city_title,
                    'relation':   user.get('relation')
            }
        except (ApiError, KeyError, ValueError) as e:
            print(f"[VK] ❌ Ошибка при получении данных пользователя {user_id}: {e}")
            return None  # Возвращаем None при ошибке

    def search_users(self, params: dict, count: int = 30) -> list:
        """Поиск пользователей по критериям"""
        try:
            search_params = {
                    'count':     count,
                    'age_from':  max(18, params.get('age_from', 18)),
                    'age_to':    min(99, params.get('age_to', 99)),
                    'sex':       1 if params.get('sex') == 2 else 2,
                    'has_photo': 1,
                    'status':    6,
                    'fields':    'sex,bdate,city,domain',  # Добавлены поля
                    'v':         API_VERSION
            }

            if 'city_id' in params and params['city_id']:
                search_params['city'] = params['city_id']

            time.sleep(0.5)
            response = self.api.users.search(**search_params)

            candidates = []
            for user in response['items']:
                if user.get('is_closed', True) and not user.get('can_access_closed', False):
                    continue

                # Получаем дополнительные данные
                city_id = user.get('city', {}).get('id')
                city_title = user.get('city', {}).get('title')
                age = self.calculate_age(user.get('bdate'))

                candidates.append({
                        'id':           user['id'],
                        'name':         f"{user['first_name']} {user['last_name']}",
                        'profile_link': f"https://vk.com/{user.get('domain', 'id' + str(user['id']))}",
                        'age':          age,
                        'gender':       user.get('sex'),
                        'city_id':      city_id,
                        'city_title':   city_title
                })
            return candidates
        except ApiError as e:
            print(f"Ошибка поиска пользователей: {e}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return []

    def get_top_photos(self, user_id: int, count: int = 3) -> list:
        try:
            time.sleep(0.3)
            response = self.api.photos.get(
                owner_id=user_id,
                album_id='profile',
                extended=1,
                count=100
            )
            photos = sorted(
                response['items'],
                key=lambda x: x['likes']['count'],
                reverse=True
            )[:count]
            return [
                f"photo{photo['owner_id']}_{photo['id']}"
                for photo in photos
            ]
        except ApiError as e:
            print(f"Ошибка получения фотографий: {e}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return []

    @staticmethod
    def calculate_age(bdate: str) -> int:
        if not bdate or len(bdate.split('.')) < 3:
            return None
        try:
            birth_date = datetime.strptime(bdate, "%d.%m.%Y")
            today = datetime.now()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except ValueError:
            return None

    def find_city(self, city_name: str) -> dict:
        try:
            time.sleep(0.3)
            response = self.api.database.getCities(
                country_id=1,
                q=city_name,
                count=10,
                need_all=0,
                v=self.api_version
            )
            return {item['title']: item['id'] for item in response['items']}
        except ApiError as e:
            print(f"Ошибка поиска города: {e}")
            return {}
        except Exception as e:
            print(f"Неожиданная ошибка при поиске города: {e}")
            return {}