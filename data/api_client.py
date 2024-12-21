import asyncio
import aiohttp
import os
import logging
from typing import Any, List, Dict, Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self):
        self.base_url = os.getenv("TEST_API_URL")
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_cache = {}
        self._token_refresh_lock = asyncio.Lock()

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _get_headers(self, telegram_id: int = None) -> dict:
        """Get headers with auth token if available"""
        headers = {"Content-Type": "application/json"}
        if telegram_id and (token := self._get_cached_token(telegram_id)):
            headers["Authorization"] = f"Token {token}"
        return headers

    def _get_cached_token(self, telegram_id: int) -> Optional[str]:
        if telegram_id in self._auth_cache:
            token_data = self._auth_cache[telegram_id]
            if datetime.now() < token_data["expires_at"]:
                return token_data["token"]
        return None

    def _store_token(self, telegram_id: int, token: str):
        """Store token with expiration"""
        self._auth_cache[telegram_id] = {
            "token": token,
            "expires_at": datetime.now() + timedelta(hours=23),
        }

    def set_student_token(self, token: str, telegram_id: int):
        """Set the student token and telegram_id for authenticated requests"""
        self._student_token = token
        self._telegram_id = telegram_id

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def refresh_token(self, telegram_id: int) -> bool:
        """Refresh authentication token"""
        if not telegram_id:
            return False

        async with self._token_refresh_lock:
            try:
                session = await self.get_session()
                url = f"{self.base_url}/students/refresh_token/"
                payload = {"telegram_id": str(telegram_id)}

                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if token := data.get("token"):
                            self._store_token(telegram_id, token)
                            return True
                    return False
            except Exception as e:
                logger.error(f"Token refresh error: {e}")
                return False

    async def ensure_authenticated(self, telegram_id: int, name: str = None) -> bool:
        """Ensure user is authenticated, refresh token if needed"""
        if not telegram_id:
            logger.error("Missing telegram_id for authentication")
            return False

        # Check cached token first
        if self._get_cached_token(telegram_id):
            return True

        if not name:
            logger.error("Name is required for initial authentication")
            return False

        try:
            session = await self.get_session()
            url = f"{self.base_url}/students/authenticate/"
            payload = {
                "telegram_id": str(telegram_id),
                "name": name
            }

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if token := data.get("token"):
                        self._store_token(telegram_id, token)
                        return True
                logger.error(f"Authentication failed: {await response.text()}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    async def make_authenticated_request(
        self, method: str, url: str, telegram_id: int, **kwargs
    ):
        """Make authenticated request with session management"""
        if not telegram_id:
            return None

        session = await self.get_session()
        headers = self._get_headers(telegram_id)
        kwargs["headers"] = headers

        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 401:
                    # Try to refresh authentication
                    if await self.ensure_authenticated(telegram_id):
                        headers = self._get_headers(telegram_id)
                        kwargs["headers"] = headers
                        async with session.request(
                            method, url, **kwargs
                        ) as retry_response:
                            return (
                                await retry_response.json()
                                if retry_response.status == 200
                                else None
                            )
                return await response.json() if response.status == 200 else None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    async def authenticate_user(self, telegram_id: int, name: str = None) -> bool:
        if not telegram_id:
            return False

        try:
            session = await self.get_session()
            url = f"{self.base_url}/students/authenticate/"

            # Check cached token first
            if self._get_cached_token(telegram_id):
                return True

            payload = {"telegram_id": str(telegram_id)}
            if name:
                payload["name"] = name

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    if token := data.get("token"):
                        self._store_token(telegram_id, token)
                        return True
                logger.error(f"Authentication failed: {await response.text()}")
                return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def get_mentors(self, telegram_id: int) -> list:
        """Get mentors with proper session management"""
        if not telegram_id:
            logger.error("telegram_id is required for get_mentors")
            return []

        try:
            return (
                await self.make_authenticated_request(
                    "GET", f"{self.base_url}/mentors/", telegram_id=telegram_id
                )
                or []
            )
        except Exception as e:
            logger.error(f"Error fetching mentors: {e}")
            return []

    # Add context manager support
    async def __aenter__(self):
        await self.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def create_student(self, student_data: dict) -> Optional[Dict]:
        url = f"{self.base_url}/students/"
        session = await self.get_session()
        try:
            async with session.post(url, json=student_data) as response:
                if response.status == 201:
                    return await response.json()
                logger.error(f"Failed to create student: {response.status}")
                return None
        except Exception as e:
            logger.error(f"Error creating student: {e}")
            return None

    async def get_student_by_telegram_id(self, telegram_id: str) -> Optional[Dict]:
        """Get student details by Telegram ID."""
        url = f"{self.base_url}/students/?telegram_id={telegram_id}"
        session = await self.get_session()
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[0] if data else None
                return None
        except Exception as e:
            logger.error(f"Error getting student: {e}")
            return None

    async def update_student(
        self, student_id: int, update_data: Dict
    ) -> Optional[Dict]:
        """Update existing student information."""
        session = await self.get_session()
        try:
            async with session.patch(
                f"{self.base_url}/students/{student_id}/",
                json=update_data,
                headers=self._get_headers(),
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error updating student {student_id}: {e}")
            return None

    async def get_mentor_by_name(self, name: str) -> Optional[Dict]:
        session = await self.get_session()
        try:
            async with session.get(f"{self.base_url}/mentors/") as response:
                if response.status == 200:
                    mentors = await response.json()
                    return next(
                        (m for m in mentors if m["name"].lower() == name.lower()), None
                    )
                return None
        except Exception as e:
            logger.error(f"Error fetching mentor by name: {e}")
            return None

    async def get_mentor_by_id(self, mentor_id: int) -> Optional[Dict]:
        """Get a mentor by ID."""
        session = await self.get_session()
        try:
            async with session.get(
                f"{self.base_url}/mentors/{mentor_id}/", headers=self._get_headers()
            ) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as e:
            logger.error(f"Error fetching mentor {mentor_id}: {e}")
            return None

    async def get_mentor_id_by_name(self, name: str) -> Optional[int]:
        mentor = await self.get_mentor_by_name(name)
        return mentor.get("id") if mentor else None

    async def get_courses_by_mentor_id(self, mentor_id: int) -> Optional[List[Dict]]:
        """Get courses by a specific mentor ID."""
        session = await self.get_session()
        try:
            async with session.get(
                f"{self.base_url}/courses/", headers=self._get_headers()
            ) as response:
                response.raise_for_status()
                courses = await response.json()
                return [course for course in courses if course["mentor"] == mentor_id]
        except Exception as e:
            logger.error(f"Error fetching courses for mentor {mentor_id}: {e}")
            return None

    async def get_course_by_id(
        self, course_id: int, telegram_id: int
    ) -> Optional[Dict]:
        """
        Get course details by ID.

        Args:
            course_id: ID of the course to fetch
            telegram_id: Telegram ID of the user making the request
        """
        if not telegram_id:
            logger.error("telegram_id is required for get_course_by_id")
            return None

        try:
            return await self.make_authenticated_request(
                "GET", f"{self.base_url}/courses/{course_id}/", telegram_id=telegram_id
            )
        except Exception as e:
            logger.error(f"Error fetching course {course_id}: {e}")
            return None

    async def get_lessons_by_course_id(
        self, course_id: int, telegram_id: int
    ) -> List[Dict]:
        """Fetch lessons by course ID."""
        try:
            course = await self.get_course_by_id(course_id, telegram_id)
            return course.get("lessons", []) if course else []
        except Exception as e:
            logger.error(f"Error fetching lessons for course {course_id}: {e}")
            return []

    async def check_user_purchase(self, telegram_id: int, course_id: int, name: str = None) -> bool:
        """Check if user has purchased a course"""
        if not await self.ensure_authenticated(telegram_id, name):
            logger.error("Failed to authenticate user for purchase check")
            return False

        try:
            result = await self.make_authenticated_request(
                "GET",
                f"{self.base_url}/payments/",
                telegram_id=telegram_id,
                params={
                    "telegram_id": telegram_id,
                    "course": course_id,
                    "status": "confirmed"
                }
            )
            return bool(result and result.get("results"))
        except Exception as e:
            logger.error(f"Error checking user purchase: {e}")
            return False

    async def create_payment(
        self, student_id: int, course_id: int, amount: float, telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """Create payment with authentication"""
        # Ensure authentication before creating payment
        if not await self.ensure_authenticated(telegram_id,):
            logger.error("Failed to authenticate user for payment creation")
            return None

        try:
            return await self.make_authenticated_request(
                "POST",
                f"{self.base_url}/payments/",
                telegram_id=telegram_id,
                json={
                    "student": student_id,
                    "course": course_id,
                    "amount": str(amount),
                },
            )
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return None
