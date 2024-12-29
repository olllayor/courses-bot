# utils/state_utils.py
from aiogram.fsm.context import FSMContext
import logging

logger = logging.getLogger(__name__)


async def get_course_id(state: FSMContext) -> int:
    """
    Retrieve the course_id from the FSM state.

    Args:
        state: The FSM context.

    Returns:
        The course_id if found, otherwise None.
    """
    try:
        state_data = await state.get_data()
        course_id = state_data.get("course_id")
        if not course_id:
            logger.warning("No course_id found in state")
            return None
        return course_id
    except Exception as e:
        logger.error(f"Error retrieving course_id: {e}")
        return None