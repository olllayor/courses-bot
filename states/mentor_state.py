# states/mentor_state.py
from aiogram.fsm.state import State, StatesGroup

class MentorState(StatesGroup):
    Mentor_ID = State()

class CourseState(StatesGroup):
    Course_ID = State()
    Viewing_Lessons = State()  # New state for when viewing lessons

class LessonState(StatesGroup):
    Lesson_ID = State()
    AWAITING_PAYMENT = State()
    Viewing_Content = State()  # New state for when viewing lesson content

