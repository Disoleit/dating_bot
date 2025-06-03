from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def get_main_keyboard():
    """Основная клавиатура"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Следующий', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('В избранное', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('Избранное', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Помощь', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def get_empty_keyboard():
    """Пустая клавиатура (скрывает предыдущую)"""
    return VkKeyboard.get_empty_keyboard()