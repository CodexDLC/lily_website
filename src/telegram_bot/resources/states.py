"""
FSM States для Telegram Bot.
Определяет состояния конечного автомата для навигации по игровым доменам.
"""

from aiogram.fsm.state import State, StatesGroup


# --- Configuration Lists ---

# Список состояний, где текстовые сообщения от юзера считаются мусором (удаляются)
GARBAGE_TEXT_STATES = [

]
