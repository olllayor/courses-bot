# datas/api_client.py

import aiohttp
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from rich import print

load_dotenv()

class APIClient:
    def __init__(self):
        self.base_url = os.getenv('TEST_API_URL')
        

    async def create_student(self, student_data: Dict) -> Optional[Dict]:
        """
        Create a new student in the remote API
        
        Args:
            student_data (Dict): Dictionary containing student information
                Required keys:
                - name: str
                - telegram_id: str
                - phone_number: str (can be empty string)
                
        Returns:
            Optional[Dict]: Created student data or None if creation fails
        """
        try:
            # Prepare the data
            payload = {
                "name": student_data["name"],
                "telegram_id": str(student_data["telegram_id"]),
                "phone_number": student_data.get("phone_number", "")
            }
            
            print(f"Attempting to create student with data: {payload}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/students/",  # Added /api/ prefix
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                ) as response:
                    print(f"Student creation response status: {response.status}")
                    
                    if response.status == 400:
                        error_data = await response.text()
                        print(f"API Error response: {error_data}")
                        
                    if response.status == 409:  # Conflict - student already exists
                        return await self.get_student_by_telegram_id(payload["telegram_id"])
                        
                    response.raise_for_status()
                    result = await response.json()
                    print(f"Student creation result: {result}")
                    return result
                    
        except aiohttp.ClientError as e:
            print(f"Error creating student: {e}")
            error_msg = str(e)
            if hasattr(e, 'message'):
                error_msg = e.message
            elif hasattr(e, 'status'):
                error_msg = f"Status: {e.status}, Message: {await e.text()}"
            print(f"Detailed error: {error_msg}")
            return None
        except Exception as e:
            print(f"Unexpected error creating student: {e}")
            return None

    async def get_student_by_telegram_id(self, telegram_id: str) -> Optional[Dict]:
        """Get student details by Telegram ID"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/students/") as response:  # Added /api/ prefix
                    response.raise_for_status()
                    students = await response.json()
                    return next(
                        (s for s in students if str(s['telegram_id']) == str(telegram_id)),
                        None
                    )
        except aiohttp.ClientError as e:
            print(f"Error fetching student by telegram_id {telegram_id}: {e}")
            return None

    async def update_student(self, student_id: int, update_data: Dict) -> Optional[Dict]:
        """Update existing student information"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/students/{student_id}/",
                    json=update_data
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error updating student {student_id}: {e}")
            return None
        

    async def get_mentors(self) -> List[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/mentors/") as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error fetching mentors: {e}")
            return []
    
    async def get_mentor_by_name(self, name: str) -> Optional[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/mentors/") as response:
                    response.raise_for_status()
                    mentors = await response.json()
                    return next((m for m in mentors if m['name'].lower() == name.lower()), None)
        except aiohttp.ClientError as e:
            print(f"Error fetching mentor by name: {e}")
            return None
        
    async def get_mentor_by_id(self, mentor_id: int) -> Optional[Dict]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/mentors/{mentor_id}/") as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error fetching mentor {mentor_id}: {e}")
            return None
            
    async def get_mentor_availability(self, mentor_id: int) -> Optional[List[Dict]]:
        mentor = await self.get_mentor_by_id(mentor_id)
        return mentor.get('availability') if mentor else None
    
    async def get_mentor_id_by_name(self, name: str) -> Optional[int]:
        mentor = await self.get_mentor_by_name(name)
        return mentor.get('id') if mentor else None
    
    async def get_courses_by_mentor_id(self, mentor_id: int) -> Optional[List[Dict]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/courses/") as response:
                    response.raise_for_status()
                    courses = await response.json()
                    # Filter courses by mentor_id
                    return [course for course in courses if course['mentor'] == mentor_id]
        except aiohttp.ClientError as e:
            print(f"Error fetching courses for mentor {mentor_id}: {e}")
            return None

    async def get_course_id_by_mentor_id(self, mentor_id: int, courses: List[Dict]) -> Optional[List[int]]:
        try:
            mentor_courses = [course['id'] for course in courses if course['mentor'] == mentor_id]
            return mentor_courses if mentor_courses else None
        except Exception as e:
            print(f"Error getting course IDs: {e}")
            return None

    async def get_course_by_title(self, title: str, courses: List[Dict]) -> Optional[Dict]:
        try:
            return next(
                (course for course in courses 
                 if course['title'].lower() == title.lower()),
                None
            )
        except Exception as e:
            print(f"Error getting course by title: {e}")
            return None

    # New methods for handling lessons

    async def get_course_by_id(self, course_id: int) -> Optional[Dict]:
        """Get course by ID including its lessons"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/courses/") as response:
                    response.raise_for_status()
                    courses = await response.json()
                    return next((c for c in courses if c['id'] == course_id), None)
        except aiohttp.ClientError as e:
            print(f"Error fetching course {course_id}: {e}")
            return None

    async def get_lessons_by_course_id(self, course_id: int) -> Optional[List[Dict]]:
        """Get all lessons for a specific course"""
        try:
            course = await self.get_course_by_id(course_id)
            if course:
                return course.get('lessons', [])
            return []
        except Exception as e:
            print(f"Error fetching lessons for course {course_id}: {e}")
            return []

    async def get_lesson_by_id(self, lesson_id: int) -> Optional[Dict]:
        """Get a specific lesson by ID"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/lessons/") as response:
                    response.raise_for_status()
                    lessons = await response.json()
                    return next((l for l in lessons if l['id'] == lesson_id), None)
        except aiohttp.ClientError as e:
            print(f"Error fetching lesson {lesson_id}: {e}")
            return None

    async def get_free_lessons_by_course_id(self, course_id: int) -> List[Dict]:
        """Get all free lessons for a specific course"""
        lessons = await self.get_lessons_by_course_id(course_id)
        return [lesson for lesson in lessons if lesson.get('is_free', False)]

    async def get_premium_lessons_by_course_id(self, course_id: int) -> List[Dict]:
        """Get all premium lessons for a specific course"""
        lessons = await self.get_lessons_by_course_id(course_id)
        return [lesson for lesson in lessons if not lesson.get('is_free', False)]
    
    async def add_user_purchase(self, user_id: int, course_id: int):
    # Add purchase record to databas
        ...

    async def create_payment(self, student_id: int, course_id: int, amount: float) -> Optional[Dict]:
        """Create a new payment record"""
        try:
            # First get course details
            course = await self.get_course_by_id(course_id)
            if not course:
                print(f"Course {course_id} not found")
                return None
                
            # Get student details (you'll need to add this method)
            student = await self.get_student_by_id(student_id)
            if not student:
                print(f"Student {student_id} not found")
                return None
                
            payment_data = {
                "student": student_id,
                "course": course_id,
                "amount": str(amount),  # Convert amount to string
                "status": "pending",
                "course_details": {
                    "mentor": course.get('mentor'),
                    "title": course.get('title'),
                    "description": course.get('description'),
                    "price": str(course.get('price'))  # Convert price to string
                },
                "student_details": {
                    "name": student.get('name'),
                    "phone_number": student.get('phone_number')
                }
            }
            
            print(f"Attempting to create payment with data: {payment_data}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/payments/", 
                    json=payment_data
                ) as response:
                    print(f"Payment creation response status: {response.status}")
                    response.raise_for_status()
                    result = await response.json()
                    print(f"Payment creation result: {result}")
                    return result
                    
        except aiohttp.ClientError as e:
            print(f"Error creating payment: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error creating payment: {e}")
            return None

    # Add this new method to get student details
    async def get_student_by_id(self, student_id: int) -> Optional[Dict]:
        """Get student details by ID"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/students/{student_id}/") as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error fetching student {student_id}: {e}")
            return None

    async def confirm_payment(self, payment_id: int) -> bool:
        """Confirm a payment"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/payments/{payment_id}/", 
                    json={"status": "confirmed"}
                ) as response:
                    response.raise_for_status()
                    return True
        except aiohttp.ClientError as e:
            print(f"Error confirming payment: {e}")
            return False

    async def check_user_purchase(self, student_id: int, course_id: int) -> bool:
        """Check if user has purchased the course"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/payments/") as response:
                    response.raise_for_status()
                    payments = await response.json()
                    return any(
                        p['student'] == student_id and 
                        p['course'] == course_id and 
                        p['status'] == 'confirmed' 
                        for p in payments
                    )
        except aiohttp.ClientError as e:
            print(f"Error checking purchase: {e}")
            return False
