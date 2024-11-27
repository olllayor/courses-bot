import aiohttp
import os
from typing import Any, List, Dict, Optional
from dotenv import load_dotenv
from rich import print

load_dotenv()

class APIClient:
    def __init__(self):
        self.base_url = os.getenv('TEST_API_URL')
        self._token = {}

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
            payload = {
                "name": student_data["name"],
                "telegram_id": student_data["telegram_id"],
                "phone_number": student_data.get("phone_number", "")
            }
            print(f"[bold green]Attempting to create student with data: {payload}[/bold green]")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/students/",
                    json=payload,
                    headers={"Content-Type": "application/json", "Accept": "application/json"}
                ) as response:
                    print(f"Student creation response status: {response.status}")

                    if response.status == 400:
                        error_data = await response.text()
                        print(f"[red]API Error response: {error_data}[/red]")
                        return None

                    if response.status == 409:  # Conflict - student already exists
                        return await self.get_student_by_telegram_id(payload["telegram_id"])

                    response.raise_for_status()
                    result = await response.json()
                    print(f"[bold green]Student creation result: {result}[/bold green]")
                    return result

        except aiohttp.ClientError as e:
            print(f"[red]Error creating student: {e}[/red]")
            return None
        except Exception as e:
            print(f"[red]Unexpected error creating student: {e}[/red]")
            return None
        
    async def authenticate_user(self, telegram_id: int, name: str) -> Optional[str]:
        """Authenticate user and get token"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/students/authenticate/",
                    json={
                        "telegram_id": telegram_id,
                        "name": name
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        token = data.get('token')
                        if token:
                            self._tokens[telegram_id] = token
                            return token
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
        
    def _get_headers(self, telegram_id: int) -> Dict[str, str]:
        """Get headers with auth token if available"""
        headers = {"Content-Type": "application/json"}
        if token := self._tokens.get(telegram_id):
            headers["Authorization"] = f"Token {token}"
        return headers

    async def get_student_by_telegram_id(self, telegram_id: str) -> Optional[Dict]:
        """Get student details by Telegram ID."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/students/") as response:
                    response.raise_for_status()
                    students = await response.json()
                    return next((s for s in students if str(s['telegram_id']) == str(telegram_id)), None)
        except aiohttp.ClientError as e:
            print(f"[red]Error fetching student by telegram_id {telegram_id}: {e}[/red]")
            return None

    async def update_student(self, student_id: int, update_data: Dict) -> Optional[Dict]:
        """Update existing student information."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(
                    f"{self.base_url}/students/{student_id}/",
                    json=update_data
                ) as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"[red]Error updating student {student_id}: {e}[/red]")
            return None

    async def get_mentors(self) -> List[Dict]:
        """Fetch a list of mentors."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/mentors/") as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"[red]Error fetching mentors: {e}[/red]")
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
        """Get a mentor by ID."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/mentors/{mentor_id}/") as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"[red]Error fetching mentor {mentor_id}: {e}[/red]")
            return None
    
    async def get_mentor_id_by_name(self, name: str) -> Optional[int]:
        mentor = await self.get_mentor_by_name(name)
        return mentor.get('id') if mentor else None

    async def get_courses_by_mentor_id(self, mentor_id: int) -> Optional[List[Dict]]:
        """Get courses by a specific mentor ID."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/courses/") as response:
                    response.raise_for_status()
                    courses = await response.json()
                    return [course for course in courses if course['mentor'] == mentor_id]
        except aiohttp.ClientError as e:
            print(f"[red]Error fetching courses for mentor {mentor_id}: {e}[/red]")
            return None

    async def get_course_by_id(self, course_id: int) -> Optional[Dict]:
        """Get course details by ID."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/courses/{course_id}/") as response:
                    response.raise_for_status()
                    return await response.json()
        except aiohttp.ClientError as e:
            print(f"[red]Error fetching course {course_id}: {e}[/red]")
            return None

    async def get_lessons_by_course_id(self, course_id: int) -> List[Dict]:
        """Fetch lessons by course ID."""
        try:
            course = await self.get_course_by_id(course_id)
            return course.get('lessons', []) if course else []
        except Exception as e:
            print(f"[red]Error fetching lessons for course {course_id}: {e}[/red]")
            return []

    async def create_payment(self, student_id: int, course_id: int, amount: float) -> Optional[Dict[str, Any]]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/payments/",
                    headers=self._get_headers(student_id),
                    json={
                        "student": student_id,
                        "course": course_id,
                        "amount": amount
                    }
                ) as response:
                    if response.status == 201:
                        return await response.json()
            return None
        except Exception as e:
            print(f"Error creating payment: {e}")
            return None


    async def check_user_purchase(self, telegram_id: int, course_id: int) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/payments/",
                    headers=self._get_headers(telegram_id),
                    params={"course": course_id}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return any(
                            payment["status"] == "confirmed" 
                            for payment in data
                        )
            return False
        except Exception as e:
            print(f"Error checking user purchase: {e}")
            return False