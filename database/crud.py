from sqlalchemy.orm import sessionmaker
from .models import Users, Candidates, Photos, Interactions, UsersCandidates
from .databasework import engine

Session = sessionmaker(bind=engine)


def add_user(session, vk_id, name, age, gender, city_id, city_title):
    try:
        # Проверяем существование пользователя
        existing_user = session.query(Users).filter_by(vk_id=vk_id).first()
        if existing_user:
            print(f"[CRUD] Пользователь {vk_id} уже существует в БД")
            return existing_user

        # Создаем нового пользователя с защитой от None
        new_user = Users(
                vk_id=vk_id,
                name=name or "Неизвестно",
                age=age or 0,
                gender=gender or "unknown",
                city_id=city_id or 0,
                city_title=city_title or "Неизвестно"
        )

        session.add(new_user)
        session.commit()
        print(f"[CRUD] ✅ Пользователь {vk_id} успешно добавлен")
        return new_user
    except Exception as e:
        session.rollback()
        print(f"[CRUD] ❌ КРИТИЧЕСКАЯ ОШИБКА при добавлении пользователя {vk_id}:")
        print(f"Данные: name={name}, age={age}, gender={gender}, city_id={city_id}, city_title={city_title}")
        print(f"Ошибка: {e}")
        print(f"Тип данных: name={type(name)}, age={type(age)}, gender={type(gender)}")
        raise


def add_candidate_with_link(session, user_vk_id, candidate_vk_id, name, age, gender, city_id, city_title, photos_data):
    try:
        # Находим пользователя
        user = session.query(Users).filter_by(vk_id=user_vk_id).first()
        if not user:
            raise ValueError(f"Пользователь с VK ID {user_vk_id} не найден")

        # Проверяем, существует ли уже кандидат
        existing_candidate = session.query(Candidates).filter_by(vk_id=candidate_vk_id).first()

        if existing_candidate:
            # Обновляем данные существующего кандидата
            if name:
                existing_candidate.name = name
            if age:
                existing_candidate.age = age
            if gender:
                existing_candidate.gender = {1: "female", 2: "male"}.get(gender, "unknown")
            if city_id:
                existing_candidate.city_id = city_id
            if city_title:
                existing_candidate.city_title = city_title

            session.flush()
        else:
            # Создаем нового кандидата с полными данными
            new_candidate = Candidates(
                    vk_id=candidate_vk_id,
                    name=name,
                    age=age,
                    gender={1: "female", 2: "male"}.get(gender, "unknown"),
                    city_id=city_id,
                    city_title=city_title
            )
            session.add(new_candidate)
            session.flush()
            existing_candidate = new_candidate

        # Обновляем или добавляем фото
        existing_photos = session.query(Photos).filter_by(candidate_id=existing_candidate.id).first()
        if existing_photos:
            # Обновляем существующие фото
            if photos_data['first_photo']:
                existing_photos.first_photo = photos_data['first_photo']
            if photos_data['second_photo']:
                existing_photos.second_photo = photos_data['second_photo']
            if photos_data['third_photo']:
                existing_photos.third_photo = photos_data['third_photo']
            if photos_data['account_link']:
                existing_photos.account_link = photos_data['account_link']
        else:
            # Добавляем новые фото
            new_photos = Photos(
                    candidate_id=existing_candidate.id,
                    first_photo=photos_data['first_photo'],
                    second_photo=photos_data['second_photo'],
                    third_photo=photos_data['third_photo'],
                    account_link=photos_data['account_link']
            )
            session.add(new_photos)

        # Создаем/обновляем связь
        existing_link = session.query(UsersCandidates).filter_by(
                user_id=user.id,
                candidate_id=existing_candidate.id
        ).first()

        if not existing_link:
            new_link = UsersCandidates(
                    user_id=user.id,
                    candidate_id=existing_candidate.id
            )
            session.add(new_link)

        session.commit()
        return existing_candidate

    except Exception as e:
        session.rollback()
        print(f"Ошибка при добавлении/обновлении кандидата: {e}")
        raise

def add_interaction(session, user_vk_id, candidate_vk_id, status):
    try:
        # Находим пользователя и кандидата
        user = session.query(Users).filter_by(vk_id=user_vk_id).first()
        if not user:
            raise ValueError(f"Пользователь с VK ID {user_vk_id} не найден")

        candidate = session.query(Candidates).filter_by(vk_id=candidate_vk_id).first()
        if not candidate:
            raise ValueError(f"Кандидат с VK ID {candidate_vk_id} не найден")

        # Проверяем, существует ли уже такое взаимодействие
        existing_interaction = session.query(Interactions).filter_by(
            user_id=user.id,
            candidate_id=candidate.id
        ).first()

        if existing_interaction:
            return existing_interaction

        # Создаем новое взаимодействие
        new_interaction = Interactions(
            user_id=user.id,
            candidate_id=candidate.id,
            status=status
        )

        session.add(new_interaction)
        session.commit()

        return new_interaction

    except Exception as e:
        session.rollback()
        print(f"Ошибка при создании взаимодействия: {e}")
        raise


def get_user_interactions_with_candidates(session, user_vk_id):
    try:
        # Находим пользователя
        user = session.query(Users).filter_by(vk_id=user_vk_id).first()
        if not user:
            raise ValueError(f"Пользователь с VK ID {user_vk_id} не найден")

        # Получаем все взаимодействия пользователя с информацией о кандидатах
        interactions = session.query(Interactions, Candidates). \
            join(Candidates, Interactions.candidate_id == Candidates.id). \
            filter(Interactions.user_id == user.id). \
            all()

        result = []
        for interaction, candidate in interactions:
            result.append({
                'candidate_id': candidate.id,
                'candidate_vk_id': candidate.vk_id,
                'candidate_name': candidate.name,
                'candidate_age': candidate.age,
                'candidate_gender': candidate.gender,
                'candidate_city': candidate.city_title,
                'interaction_id': interaction.id,
                'interaction_status': interaction.status,
                'interaction_date': interaction.created_at if hasattr(interaction, 'created_at') else None
            })

        return result

    except Exception as e:
        print(f"Ошибка при получении взаимодействий пользователя: {e}")
        raise
# Для тестирования
# if __name__ == "__main__":
#
#     try:
#         # # Создаем таблицы (если их нет)
#         Base.metadata.create_all(engine)
#
#         # Добавляем пользователя
#         user = add_user(
#             session=session,
#             vk_id=123456789,
#             name="Иван Тест",
#             age=30,
#             gender="male",
#             city_title="Москва",
#             city_id=1
#         )
#
#         # Добавляем кандидата и связываем с пользователем
#         candidate, link = add_candidate_with_link(
#             session=session,
#             user_vk_id=123456789,
#             candidate_vk_id=987654321,
#             name="Мария Тест0",
#             age=28,
#             gender="female",
#                 city_title="Москва",
#                 city_id=1,
#             photos_data={
#                 'first_photo': 'photo1.jpg',
#                 'second_photo': 'photo2.jpg',
#                 'third_photo': 'photo3.jpg',
#                 'account_link': 'https://vk.com/id987654321'
#             }
#         )
#
#     finally:
#         session.close()