from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """FSM states for user onboarding process."""

    waiting_for_language = State()
    waiting_for_bedtime = State()
    waiting_for_waketime = State()
    waiting_for_target_hours = State()
    waiting_for_timezone = State()


class StatsStates(StatesGroup):
    """FSM states for statistics export process."""

    waiting_for_period = State()
    waiting_for_format = State()
    waiting_for_custom_date_from = State()
    waiting_for_custom_date_to = State()


class NoteStates(StatesGroup):
    """FSM states for note input process."""

    waiting_for_note_text = State()
    waiting_for_note_confirmation = State()


class QualityStates(StatesGroup):
    """FSM states for quality rating confirmation."""

    waiting_for_confirmation = State()
