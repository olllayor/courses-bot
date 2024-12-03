import aiohttp
import os
from typing import Any, List, Dict, Optional
from dotenv import load_dotenv
from rich import print

load_dotenv()

class APIClient:
    def __init__(self):
        self.base_url = os.getenv('TEST_API_URL')
        self._tokens = {}

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
        url = f"{self.base_url}/students/"
        headers = self._get_headers(student_data.get('telegram_id'))
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=student_data) as response:
                    if response.status == 201:
                        return await response.json()
                    else:
                        print(f"[red]Failed to create student: {response.status} {response.reason}[/red]")
                        return None
            except aiohttp.ClientError as e:
                print(f"[red]ClientError during create_student: {e}[/red]")
                return None
            except Exception as e:
                print(f"[red]Unexpected error during create_student: {e}[/red]")
                return None

    async def authenticate_user(self, telegram_id: int, name: str) -> Optional[str]:
        """Authenticate user and get token"""
        url = f"{self.base_url}/students/authenticate/"
        payload = {
            "telegram_id": telegram_id,
            "name": name
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        token = data.get('token')
                        if token:
                            self._tokens[telegram_id] = token
                            return token
                        else:
                            print("[red]Authentication failed: No token returned[/red]")
                            return None
                    else:
                        print(f"[red]Authentication failed: {response.status} {response.reason}[/red]")
                        return None
            except aiohttp.ClientError as e:
                print(f"[red]ClientError during authenticate_user: {e}[/red]")
                return None
            except Exception as e:
                print(f"[red]Unexpected error during authenticate_user: {e}[/red]")
                return None

    def _get_headers(self, telegram_id: int) -> Dict[str, str]:
        """Get headers with auth token if available"""
        headers = {"Content-Type": "application/json"}
        token = self._tokens.get(telegram_id)
        if token:
            headers["Authorization"] = f"Token {token}"
        return headers

    async def get_student_by_telegram_id(self, telegram_id: str) -> Optional[Dict]:
        """Get student details by Telegram ID."""
        url = f"{self.base_url}/students/?telegram_id={telegram_id}"
        headers = self._get_headers(int(telegram_id))
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"[red]Failed to get student: {response.status} {response.reason}[/red]")
                        return None
            except aiohttp.ClientError as e:
                print(f"[red]ClientError during get_student_by_telegram_id: {e}[/red]")
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