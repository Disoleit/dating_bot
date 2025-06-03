import vk_api
from vk_api.exceptions import ApiError
from datetime import datetime
from config import USER_TOKEN, API_VERSION
import time


class VKTools:

    def __init__(self):
        self.user_vk = vk_api.VkApi(token=USER_TOKEN, api_version=API_VERSION)
        self.api = self.user_vk.get_api()

    def get_user_info(self, user_id: int) -> dict:
        """Получение информации о пользователе"""
        try:
            response = self.api.users.get(
                    user_ids=user_id,
                    fields='sex,bdate,city,relation'
            )
            if not response:
                return {}

            user = response[0]
            city_id = user.get('city', {}).get('id')
            city_title = user.get('city', {}).get('title') if city_id else None

            return {
                    'id':         user['id'],
                    'name':       f"{user.get('first_name', '')} {user.get('last_name', '')}",
                    'sex':        user.get('sex'),
                    'age':        self.calculate_age(user.get('bdate')),
                    'city_id':    city_id,
                    'city_title': city_title,
                    'relation':   user.get('relation')
            }
        except (ApiError, KeyError, ValueError) as e:
            print(f"Ошибка при получении данных пользователя: {e}")
            return {}

    def search_users(self, params: dict, count: int = 30) -> list:
        """Поиск пользователей по критериям"""
        try:
            # Формируем параметры поиска
            search_params = {
                    'count':     count,
                    'age_from':  max(18, params.get('age', 25) - 5),
                    'age_to':    min(99, params.get('age', 30) + 5),
                    'sex':       1 if params.get('sex') == 2 else 2,
                    'has_photo': 1,
                    'status':    6,  # В активном поиске
                    'fields':    'domain',
                    'v':         API_VERSION
            }

            if 'city_id' in params and params['city_id']:
                search_params['city'] = params['city_id']

            # Задержка для соблюдения лимитов API
            time.sleep(0.5)

            response = self.api.users.search(**search_params)
            return [
                    {
                            'id':           user['id'],
                            'name':         f"{user['first_name']} {user['last_name']}",
                            'profile_link': f"https://vk.com/{user.get('domain', 'id' + str(user['id']))}",
                    }
                    for user in response['items']
                    if not user.get('is_closed', True)
            ]
        except ApiError as e:
            print(f"Ошибка поиска пользователей: {e}")
            return []
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return []

    def get_top_photos(self, user_id: int, count: int = 3) -> list:
        """Получение топ-3 популярных фотографий"""
        try:
            # Задержка для соблюдения лимитов API
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
        """Вычисление возраста по дате рождения"""
        if not bdate or len(bdate.split('.')) < 3:
            return None
        try:
            birth_date = datetime.strptime(bdate, "%d.%m.%Y")
            today = datetime.now()
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        except ValueError:
            return None