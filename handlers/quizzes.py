import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton
from data.api_client import APIClient
from states.quiz_state import QuizState

router = Router()
api_client = APIClient()
logger = logging.getLogger(__name__)

def create_quiz_keyboard(lesson_id):
    """Create keyboard with quiz button"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✏️ Take Quiz",
        callback_data=f"start_quiz_{lesson_id}"
    ))
    return builder.as_markup()

def create_answer_keyboard(answers, question_idx):
    """Create keyboard with answer options"""
    builder = InlineKeyboardBuilder()
    for idx, answer in enumerate(answers):
        builder.add(InlineKeyboardButton(
            text=answer,
            callback_data=f"quiz_answer_{question_idx}_{idx}"
        ))
    builder.adjust(1)  # One button per row
    return builder.as_markup()

@router.callback_query(lambda c: c.data.startswith("start_quiz_"))
async def start_quiz(callback: CallbackQuery, state: FSMContext):
    """Start a quiz for a specific lesson"""
    lesson_id = int(callback.data.split("_")[2])
    user_id = callback.from_user.id
    
    try:
        # Get quiz for this lesson
        quizzes = await api_client.make_request(
            "GET", f"{api_client.base_url}/quizzes/?lesson={lesson_id}"
        )
        
        if not quizzes or len(quizzes) == 0:
            await callback.message.answer("No quizzes found for this lesson!")
            await callback.answer()
            return
        
        # Take the first quiz
        quiz = quizzes[0]
        
        # Save quiz data in state
        await state.update_data(
            quiz_id=quiz["id"],
            lesson_id=lesson_id,
            questions=quiz["questions"],
            answers=quiz["answers"],
            correct_answers=quiz["correct_answers"],
            current_question=0,
            user_answers=[],
            score=0
        )
        
        # Show first question
        await show_question(callback.message, state)
        await state.set_state(QuizState.Answering)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error starting quiz: {e}")
        await callback.message.answer("Error loading quiz. Please try again later.")
        await callback.answer()

async def show_question(message, state: FSMContext):
    """Show the current question to the user"""
    data = await state.get_data()
    question_idx = data["current_question"]
    
    if question_idx >= len(data["questions"]):
        # All questions answered, show results
        await show_results(message, state)
        return
    
    question = data["questions"][question_idx]
    answers = data["answers"][question_idx]
    
    # Display question with answers as keyboard buttons
    await message.answer(
        f"Question {question_idx+1}/{len(data['questions'])}: {question}",
        reply_markup=create_answer_keyboard(answers, question_idx)
    )

@router.callback_query(QuizState.Answering, lambda c: c.data.startswith("quiz_answer_"))
async def process_answer(callback: CallbackQuery, state: FSMContext):
    """Process user's answer"""
    # Parse callback data more safely
    parts = callback.data.split("_")
    # We need at least "quiz", "answer", question_idx, answer_idx
    if len(parts) < 4:
        logger.error(f"Invalid callback data format: {callback.data}")
        await callback.answer("Error processing answer")
        return
        
    question_idx = int(parts[2])
    answer_idx = int(parts[3])
    
    logger.info(f"Processing answer: question {question_idx}, choice {answer_idx}")
    
    data = await state.get_data()
    user_answers = data["user_answers"]
    
    # Record the answer
    if question_idx >= len(user_answers):
        user_answers.append(answer_idx)
    else:
        user_answers[question_idx] = answer_idx
        
    # Check if the answer is correct
    correct_answers = data["correct_answers"]
    if question_idx < len(correct_answers) and answer_idx == correct_answers[question_idx]:
        data["score"] += 1
        await callback.answer("✅ Correct!")
    else:
        await callback.answer("❌ Incorrect!")
    
    # Update state
    data["user_answers"] = user_answers
    data["current_question"] = question_idx + 1
    await state.update_data(**data)
    
    # Show next question
    await show_question(callback.message, state)

async def show_results(message, state: FSMContext):
    """Show quiz results and save progress"""
    data = await state.get_data()
    user_id = message.chat.id
    quiz_id = data["quiz_id"]
    lesson_id = data["lesson_id"]
    score = data["score"]
    total_questions = len(data["questions"])
    
    # Calculate percentage
    percentage = (score / total_questions) * 100
    perfect_score = (percentage == 100)
    
    # Create result message
    result_message = f"Quiz completed!\n\nYour score: {score}/{total_questions} ({percentage:.1f}%)"
    
    # Add perfect score message if applicable
    if perfect_score:
        result_message += "\n\n🏆 Perfect score! You've unlocked the next lesson."
    
    await message.answer(result_message)
    
    # Update student progress
    try:
        # Check if user exists in the system
        user_info = await api_client.make_request(
            "GET", 
            f"{api_client.base_url}/students/",
            params={"telegram_id": user_id}
        )
        
        if user_info and isinstance(user_info, list) and len(user_info) > 0:
            student_id = user_info[0]["id"]
            
            # Check if progress already exists
            existing_progress = await api_client.make_request(
                "GET",
                f"{api_client.base_url}/progress/",
                params={
                    "student": student_id,
                    "lesson": lesson_id
                }
            )
            
            # Create or update progress
            progress_data = {
                "student": student_id,
                "lesson": lesson_id,
                "quiz_score": score
            }
            
            if existing_progress and isinstance(existing_progress, list) and len(existing_progress) > 0:
                # Update existing progress
                progress_id = existing_progress[0]["id"]
                await api_client.make_request(
                    "PUT",
                    f"{api_client.base_url}/progress/{progress_id}/",
                    json=progress_data
                )
            else:
                # Create new progress
                await api_client.make_request(
                    "POST",
                    f"{api_client.base_url}/progress/",
                    json=progress_data
                )
            
            # If perfect score, unlock next lesson by creating an "unlock" record
            if perfect_score:
                try:
                    # First, get the current lesson to find its course
                    lesson = await api_client.make_request(
                        "GET",
                        f"{api_client.base_url}/lessons/{lesson_id}/"
                    )
                    
                    if lesson and "course" in lesson:
                        course_id = lesson["course"]
                        
                        # Get all lessons for this course to find the next one
                        course = await api_client.make_request(
                            "GET",
                            f"{api_client.base_url}/courses/{course_id}/"
                        )
                        
                        if course and "lessons" in course:
                            # Sort lessons by id to determine order
                            sorted_lessons = sorted(course["lessons"], key=lambda x: x["id"])
                            
                            # Find current lesson index
                            current_index = next((i for i, l in enumerate(sorted_lessons) if l["id"] == lesson_id), -1)
                            
                            # If there's a next lesson and it's not free
                            if current_index >= 0 and current_index + 1 < len(sorted_lessons):
                                next_lesson = sorted_lessons[current_index + 1]
                                
                                if not next_lesson["is_free"]:
                                    # Create a special "unlock" progress record for the next lesson
                                    # with a special flag or high quiz score to indicate it's unlocked
                                    await api_client.make_request(
                                        "POST",
                                        f"{api_client.base_url}/progress/",
                                        json={
                                            "student": student_id,
                                            "lesson": next_lesson["id"],
                                            "quiz_score": 999,  # Special value to indicate unlocked by perfect score
                                            "unlocked_by_quiz": True  # This field might need to be added to your model
                                        }
                                    )
                                    logger.info(f"Unlocked next lesson {next_lesson['id']} for user {user_id} with perfect score")
                except Exception as e:
                    logger.error(f"Error unlocking next lesson: {e}")
            
            logger.info(f"Updated progress for user {user_id}, lesson {lesson_id}, score {score}")
            
        # Reset state
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error saving quiz progress: {e}")
        await message.answer("There was an error saving your progress.")