from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_main_keyboard():
    """Основная клавиатура"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Поиск', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Настройки', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Избранное', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Помощь', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def get_settings_keyboard():
    """Клавиатура настроек с кнопкой Поиск"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Изменить город', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Изменить возраст', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Поиск', color=VkKeyboardColor.POSITIVE)  # Добавлена кнопка Поиск
    keyboard.add_line()
    keyboard.add_button('Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

def get_search_keyboard():
    """Клавиатура во время поиска"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Следующий', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('В избранное', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Стоп поиск', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

def get_empty_keyboard():
    """Пустая клавиатура"""
    return VkKeyboard.get_empty_keyboard()