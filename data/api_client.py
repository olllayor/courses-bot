import asyncio
import aiohttp
import os
import logging
from typing import Any, List, Dict, Optional
from dotenv import load_dotenv
from datetime import datetime, timedelta
from rich import print

load_dotenv()
logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self):
        self.base_url = os.getenv("TEST_API_URL")
        self._session: Optional[aiohttp.ClientSession] = None
        self._auth_cache = {}
        self._token_refresh_lock = asyncio.Lock()
        self._token_expiry_hours = int(
            os.getenv("TOKEN_EXPIRY_HOURS", 23)
        )  # configurable token expiry

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _get_headers(self, telegram_id: int = None) -> dict:
        """Get headers with auth token if available"""
        headers = {"Content-Type": "application/json"}
        if telegram_id:
            token = self._get_cached_token(telegram_id)
            if token:
                headers["Authorization"] = (
                    f"Bearer {token}"  # Changed from Token to Bearer
                )
                logger.debug(f"Added authorization header for user {telegram_id}")
            else:
                logger.warning(f"No token found for user {telegram_id}")
        return headers

    def _get_cached_token(self, telegram_id: int) -> Optional[str]:
        if telegram_id in self._auth_cache:
            token_data = self._auth_cache[telegram_id]
            if datetime.now() < token_data["expires_at"]:
                return token_data["token"]
            else:
                logger.debug(f"Token expired for user {telegram_id}")
                del self._auth_cache[telegram_id]
        return None

    def _store_token(self, telegram_id: int, token: str):
        """Store token with expiration"""
        self._auth_cache[telegram_id] = {
            "token": token,
            "expires_at": datetime.now() + timedelta(hours=self._token_expiry_hours),
        }
        logger.debug(f"Stored new token for user {telegram_id}")

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def refresh_token(self, telegram_id: int) -> bool:
        async with self._token_refresh_lock:
            try:
                session = await self.get_session()
                url = f"{self.base_url}/students/refresh_token/"
                payload = {"telegram_id": str(telegram_id)}

                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if token := data.get("token"):
                            self._store_token(telegram_id, token)
                            logger.info(
                                f"Successfully refreshed token for user {telegram_id}"
                            )
                            return True
                    logger.error(
                        f"Token refresh failed: {response.status} - {await response.text()}"
                    )
                    return False
            except Exception as e:
                logger.error(f"Token refresh error: {e}")
                return False

        async with self._token_refresh_lock:
            try:
                session = await self.get_session()
                url = f"{self.base_url}/students/refresh_token/"
                payload = {"telegram_id": str(telegram_id)}

                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if token := data.get("token"):
                            self._store_token(telegram_id, token)
                            return True
                    else:
                        logger.error(
                            f"Token refresh failed with status: {response.status} - {await response.text()}"
                        )
                    return False
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
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
            payload = {"telegram_id": str(telegram_id), "name": name}

            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if token := data.get("token"):
                        self._store_token(telegram_id, token)
                        return True
                logger.error(f"Authentication failed: {await response.text()}")
                return False
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def make_authenticated_request(
        self, method: str, url: str, telegram_id: int, **kwargs
    ):
        if not telegram_id:
            logger.error("No telegram_id provided for authenticated request")
            return None

        session = await self.get_session()
        headers = self._get_headers(telegram_id)
        kwargs["headers"] = headers

        try:
            async with session.request(method, url, **kwargs, timeout=10) as response:
                if response.status == 401:
                    logger.info(f"Attempting token refresh for user {telegram_id}")
                    if await self.refresh_token(telegram_id):
                        # Get fresh headers after token refresh
                        kwargs["headers"] = self._get_headers(telegram_id)
                        async with session.request(
                            method, url, **kwargs, timeout=10
                        ) as retry_response:
                            if retry_response.status == 200:
                                return await retry_response.json()
                            logger.error(
                                f"Request failed after token refresh: {retry_response.status} - {await retry_response.text()}"
                            )
                            return None
                    return None

                if response.status == 200:
                    return await response.json()

                logger.error(
                    f"Request failed: {response.status} - {await response.text()}"
                )
                return None

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    async def authenticate_user(self, telegram_id: int, name: str = None) -> bool:
        try:
            session = await self.get_session()
            url = f"{self.base_url}/students/authenticate/"

            if self._get_cached_token(telegram_id):
                return True

            payload = {"telegram_id": str(telegram_id)}
            if name:
                payload["name"] = name

            async with session.post(url, json=payload, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    if token := data.get("token"):
                        self._store_token(telegram_id, token)
                        logger.info(f"User {telegram_id} authenticated successfully")
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
            async with session.post(url, json=student_data, timeout=10) as response:
                if response.status == 201:
                    return await response.json()
                logger.error(
                    f"Failed to create student: {response.status} - {await response.text()}"
                )
                return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error creating student: {e}")
            return None

    async def get_student_by_telegram_id(self, telegram_id: str) -> Optional[Dict]:
        """Get student details by Telegram ID."""
        url = f"{self.base_url}/students/?telegram_id={telegram_id}"
        session = await self.get_session()
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[0] if data else None
                logger.error(
                    f"Failed to get student: {response.status} - {await response.text()}"
                )
                return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
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
                timeout=10,
            ) as response:
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error updating student {student_id}: {e}")
            return None

    async def get_mentor_by_name(self, name: str) -> Optional[Dict]:
        session = await self.get_session()
        try:
            async with session.get(f"{self.base_url}/mentors/", timeout=10) as response:
                if response.status == 200:
                    mentors = await response.json()
                    return next(
                        (m for m in mentors if m["name"].lower() == name.lower()), None
                    )
                logger.error(
                    f"Failed to get mentor by name: {response.status} - {await response.text()}"
                )
                return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error fetching mentor by name: {e}")
            return None

    async def get_mentor_by_id(self, mentor_id: int) -> Optional[Dict]:
        """Get a mentor by ID."""
        session = await self.get_session()
        try:
            async with session.get(
                f"{self.base_url}/mentors/{mentor_id}/",
                headers=self._get_headers(),
                timeout=10,
            ) as response:
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
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
                f"{self.base_url}/courses/", headers=self._get_headers(), timeout=10
            ) as response:
                response.raise_for_status()
                courses = await response.json()
                return [
                    course for course in courses if course["mentor"]["id"] == mentor_id
                ]
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
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

    async def check_user_purchase(
        self, telegram_id: int, course_id: int, name: str = None
    ) -> bool:
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
                    "status": "confirmed",
                },
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
        if not await self.ensure_authenticated(
            telegram_id,
        ):
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

    async def get_payment_details(
        self, payment_id: int, telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get payment details with authentication"""
        try:
            return await self.make_authenticated_request(
                "GET",
                f"{self.base_url}/payments/{payment_id}/",
                telegram_id=telegram_id,
            )
        except Exception as e:
            logger.error(f"Error getting payment details: {e}")
            return None

    async def add_user_purchase(
        self, user_id: int, course_id: int, telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """Mark a payment as confirmed (for admin use)"""
        try:
            return await self.make_authenticated_request(
                "POST",
                f"{self.base_url}/payments/{user_id}/confirm/",
                telegram_id=telegram_id,
            )
        except Exception as e:
            logger.error(f"Error add user purchase: {e}")
            return None

    async def update_mentor(
        self, mentor_id: int, update_data: dict, telegram_id: int = None
    ) -> Optional[Dict]:
        """Update existing mentor information."""
        session = await self.get_session()
        try:
            async with session.patch(
                f"{self.base_url}/mentors/{mentor_id}/",
                json=update_data,
                headers=self._get_headers(telegram_id),
                timeout=10,
            ) as response:
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error updating mentor {mentor_id}: {e}")
            return None

    async def update_lesson(
        self, lesson_id: int, update_data: dict, telegram_id: int = None
    ) -> Optional[Dict]:
        """Update existing lesson information."""
        session = await self.get_session()
        try:
            async with session.patch(
                f"{self.base_url}/lessons/{lesson_id}/",
                json=update_data,
                headers=self._get_headers(telegram_id),
                timeout=10,
            ) as response:
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error(f"Error updating lesson {lesson_id}: {e}")
            return None

    async def get_webinars(
        self, telegram_id: int, mentor_id: int = None
    ) -> Optional[List[Dict]]:
        """
        Get webinars with optional mentor filter.

        Args:
            telegram_id: User's telegram ID for authentication
            mentor_id: Optional mentor ID to filter webinars

        Returns:
            List of webinar dictionaries
        """
        try:
            params = {}
            if mentor_id:
                params["mentor"] = mentor_id

            result = await self.make_authenticated_request(
                "GET",
                f"{self.base_url}/webinars/",
                telegram_id=telegram_id,
                params=params,
            )


            if isinstance(result, dict):
                # Handle paginated response
                return result.get("results", [])
            elif isinstance(result, list):
                # Handle non-paginated response
                return result
            return None

        except Exception as e:
            logger.error(f"Error fetching webinars: {e}")
            return None
