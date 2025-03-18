import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self):
        self.base_url = os.getenv("TEST_API_URL")
        self._session: Optional[aiohttp.ClientSession] = None
        self._known_users = set()  # Just store telegram_ids of known users

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def _get_headers(self) -> dict:
        """Get standard headers"""
        return {"Content-Type": "application/json"}

    def _register_user(self, telegram_id: int):
        """Register a user as known"""
        self._known_users.add(telegram_id)

    def _is_registered(self, telegram_id: int) -> bool:
        """Check if a user is registered"""
        return telegram_id in self._known_users

    async def close(self):
        """Close the session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def ensure_user_exists(self, telegram_id: int, name: str = None) -> bool:
        """Ensure user exists in the system, create if needed"""
        if not telegram_id:
            logger.error("Missing telegram_id for user registration")
            return False
        
        # Convert to int if string was passed
        if isinstance(telegram_id, str):
            try:
                telegram_id = int(telegram_id)
            except ValueError:
                logger.error(f"Invalid telegram_id format: {telegram_id}")
                return False

        # If we already know this user, return True
        if self._is_registered(telegram_id):
            return True

        try:
            logger.info(f"Checking if user {telegram_id} exists")
            session = await self.get_session()
            
            # First check if user exists
            async with session.get(f"{self.base_url}/students/?telegram_id={telegram_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        # User exists
                        self._register_user(telegram_id)
                        logger.info(f"User {telegram_id} already exists in the system")
                        return True
            
            # User doesn't exist, create if name is provided
            if name:
                logger.info(f"Creating new user {telegram_id} with name {name}")
                payload = {
                    "telegram_id": str(telegram_id),
                    "name": name
                }
                
                async with session.post(f"{self.base_url}/students/", json=payload) as response:
                    if response.status in (200, 201):
                        self._register_user(telegram_id)
                        logger.info(f"Successfully created user {telegram_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create user {telegram_id}: {response.status} - {error_text}")
                        return False
            else:
                logger.error(f"User {telegram_id} doesn't exist and no name provided to create one")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring user exists: {e}")
            return False

    async def make_request(self, method: str, url: str, telegram_id: int = None, **kwargs):
        """Make a request with telegram_id as a query parameter"""
        session = await self.get_session()
        
        # Add Content-Type header if not provided
        headers = kwargs.get('headers', {})
        headers.setdefault('Content-Type', 'application/json')
        kwargs['headers'] = headers
        
        # Add telegram_id as a query parameter for endpoints that need it
        if telegram_id is not None:
            params = kwargs.get('params', {})
            params['telegram_id'] = str(telegram_id)
            kwargs['params'] = params
        
        logger.info(f"Making request: {method} {url}")
        
        try:
            async with session.request(method, url, **kwargs) as response:
                status_code = response.status
                logger.info(f"Response status: {status_code} for {method} {url}")
                
                if status_code in (200, 201):
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Request failed with status {status_code}: {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Request failed for {method} {url}: {e}")
            return None

    # Add context manager support
    async def __aenter__(self):
        await self.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def get_mentors(self, telegram_id: int = None) -> list:
        """Get mentors list"""
        try:
            return await self.make_request("GET", f"{self.base_url}/mentors/") or []
        except Exception as e:
            logger.error(f"Error fetching mentors: {e}")
            return []

    async def get_mentor_by_name(self, name: str) -> Optional[Dict]:
        """Get mentor by name"""
        try:
            mentors = await self.make_request("GET", f"{self.base_url}/mentors/")
            if mentors:
                return next((m for m in mentors if m["name"].lower() == name.lower()), None)
            return None
        except Exception as e:
            logger.error(f"Error fetching mentor by name: {e}")
            return None

    async def get_mentor_by_id(self, mentor_id: int) -> Optional[Dict]:
        """Get a mentor by ID."""
        try:
            return await self.make_request("GET", f"{self.base_url}/mentors/{mentor_id}/")
        except Exception as e:
            logger.error(f"Error fetching mentor {mentor_id}: {e}")
            return None

    async def get_mentor_id_by_name(self, name: str) -> Optional[int]:
        """Get mentor ID by name"""
        mentor = await self.get_mentor_by_name(name)
        return mentor.get("id") if mentor else None

    async def get_courses_by_mentor_id(self, mentor_id: int) -> Optional[List[Dict]]:
        """Get courses by a specific mentor ID."""
        try:
            courses = await self.make_request("GET", f"{self.base_url}/courses/")
            if courses:
                return [course for course in courses if course["mentor"] == mentor_id]
            return []
        except Exception as e:
            logger.error(f"Error fetching courses for mentor {mentor_id}: {e}")
            return []

    async def get_course_by_id(self, course_id: int, telegram_id: int = None) -> Optional[Dict]:
        """Get course details by ID."""
        try:
            # Just make a simple request, telegram_id is passed for potential filtering
            return await self.make_request(
                "GET", 
                f"{self.base_url}/courses/{course_id}/",
                telegram_id=telegram_id
            )
        except Exception as e:
            logger.error(f"Error fetching course {course_id}: {e}")
            return None

    async def get_lessons_by_course_id(self, course_id: int, telegram_id: int = None) -> List[Dict]:
        """Fetch lessons by course ID."""
        try:
            course = await self.get_course_by_id(course_id, telegram_id)
            return course.get("lessons", []) if course else []
        except Exception as e:
            logger.error(f"Error fetching lessons for course {course_id}: {e}")
            return []

    async def check_user_purchase(self, telegram_id: int, course_id: int, name: str = None) -> bool:
        """Check if user has purchased a course"""
        if not telegram_id:
            logger.error("No telegram_id provided for purchase check")
            return False
        
        if not course_id:
            logger.error("No course_id provided for purchase check")
            return False
        
        # Ensure user exists
        if name and not await self.ensure_user_exists(telegram_id, name):
            logger.warning(f"User {telegram_id} doesn't exist, creating")
            if not await self.ensure_user_exists(telegram_id, name):
                logger.error(f"Failed to create user {telegram_id}")
                return False
        
        try:
            # Direct check for confirmed payments
            logger.info(f"Checking if user {telegram_id} has purchased course {course_id}")
            result = await self.make_request(
                "GET",
                f"{self.base_url}/payments/",
                params={
                    "telegram_id": telegram_id,
                    "course": course_id,
                    "status": "confirmed"
                }
            )
            
            # Check if any confirmed payments exist
            has_purchased = False
            if result:
                if isinstance(result, list):
                    has_purchased = len(result) > 0
                elif isinstance(result, dict) and "results" in result:
                    has_purchased = len(result.get("results", [])) > 0
            
            logger.info(f"Purchase check result for user {telegram_id}, course {course_id}: {has_purchased}")
            return has_purchased
            
        except Exception as e:
            logger.error(f"Error checking purchase: {e}")
            return False

    async def create_payment(self, student_id: int, course_id: int, amount: float, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Create payment record for a course"""
        try:
            # Ensure user exists
            user_name = None
            # Try to get user info first
            user_info = await self.make_request(
                "GET", 
                f"{self.base_url}/students/",
                params={"telegram_id": telegram_id}
            )
            if user_info and isinstance(user_info, list) and len(user_info) > 0:
                user_name = user_info[0].get("name")
                
            if not await self.ensure_user_exists(telegram_id, user_name):
                logger.error(f"User {telegram_id} doesn't exist and couldn't be created")
                return None
            
            # Check for existing pending payments first
            existing_payments = await self.make_request(
                "GET",
                f"{self.base_url}/payments/",
                params={
                    "telegram_id": telegram_id,
                    "course": course_id,
                    "status": "pending"
                }
            )
            
            # If there's a pending payment, return it instead of creating a new one
            if existing_payments and isinstance(existing_payments, list) and len(existing_payments) > 0:
                logger.info(f"Found existing pending payment for user {telegram_id}, course {course_id}")
                return existing_payments[0]
            
            # Create payment
            payment_data = {
                "student": student_id,
                "course": course_id,
                "amount": str(amount)
            }
            
            # Pass telegram_id as a parameter for server-side validation
            return await self.make_request(
                "POST",
                f"{self.base_url}/payments/",
                telegram_id=telegram_id,
                json=payment_data
            )
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            return None

    async def get_payment_details(self, payment_id: int, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get payment details by ID"""
        try:
            # Check if this is likely an admin based on ADMIN_IDS
            is_admin = str(telegram_id) in os.getenv("ADMIN_ID", "").split(",")
            logger.info(f"User {telegram_id} requesting payment {payment_id} details (admin: {is_admin})")
            
            # First attempt: Direct access with telegram_id
            result = await self.make_request(
                "GET",
                f"{self.base_url}/payments/{payment_id}/",
                telegram_id=telegram_id,
                params={"is_admin": "true"} if is_admin else {}
            )
            
            if result:
                logger.info(f"Successfully retrieved payment {payment_id} details (direct access)")
                return result
            
            # If direct access fails and this is an admin, try the general payments endpoint
            if is_admin:
                logger.info(f"Direct access failed, trying to get payment {payment_id} through list endpoint")
                payments_list = await self.make_request(
                    "GET",
                    f"{self.base_url}/payments/",
                    telegram_id=telegram_id,
                    params={"is_admin": "true"}
                )
                
                if payments_list and isinstance(payments_list, list):
                    # Find the payment in the list
                    for payment in payments_list:
                        if payment.get("id") == int(payment_id):
                            logger.info(f"Found payment {payment_id} in payments list")
                            return payment
            
            logger.error(f"Failed to retrieve payment {payment_id} details")
            return None
        except Exception as e:
            logger.error(f"Error getting payment details: {e}")
            return None

    async def confirm_payment(self, payment_id: int, telegram_id: int, name: str = None) -> bool:
        """Confirm a payment by ID by updating its status"""
        if not payment_id:
            logger.error("No payment_id provided for confirmation")
            return False
        
        try:
            # Ensure admin is registered
            if name and not await self.ensure_user_exists(telegram_id, name):
                logger.warning(f"Admin {telegram_id} not found, creating user record")
                if not await self.ensure_user_exists(telegram_id, name):
                    logger.error(f"Failed to create admin user {telegram_id}")
                    return False
            
            # Get all payments to find the one we need
            payments = await self.make_request(
                "GET",
                f"{self.base_url}/payments/",
                telegram_id=telegram_id,
                params={"is_admin": "true"}
            )
            
            target_payment = None
            if payments and isinstance(payments, list):
                for payment in payments:
                    if payment.get("id") == int(payment_id):
                        target_payment = payment
                        break
            
            if not target_payment:
                logger.error(f"Could not find payment {payment_id} in payments list")
                return False
            
            # Check if this payment is for a test user
            student_id = target_payment.get("student")
            if student_id and int(student_id) < 10000:
                logger.warning(f"Confirming payment {payment_id} for test user {student_id}")
            
            # Update the payment status to confirmed
            target_payment["status"] = "confirmed"
            
            # Send the update to the API
            result = await self.make_request(
                "PUT",
                f"{self.base_url}/payments/{payment_id}/",
                telegram_id=telegram_id,
                params={"is_admin": "true"},
                json=target_payment
            )
            
            if result:
                logger.info(f"Payment {payment_id} confirmed successfully")
                return True
            else:
                logger.error(f"Failed to confirm payment {payment_id}")
                return False
        except Exception as e:
            logger.error(f"Error confirming payment {payment_id}: {e}")
            return False

    async def cancel_payment(self, payment_id: int, telegram_id: int, name: str = None) -> bool:
        """Cancel a payment by ID"""
        if not payment_id:
            logger.error("No payment_id provided for cancellation")
            return False
        
        try:
            # Ensure user exists (important for admins)
            if name and not await self.ensure_user_exists(telegram_id, name):
                logger.warning(f"Admin {telegram_id} not found, creating user record")
                if not await self.ensure_user_exists(telegram_id, name):
                    logger.error(f"Failed to create admin user {telegram_id}")
                    return False
            
            # Try the all-payments endpoint with an action parameter
            logger.info(f"Attempting to cancel payment {payment_id} with admin ID: {telegram_id}")
            
            # First approach: Try the general payment update endpoint
            result = await self.make_request(
                "POST",
                f"{self.base_url}/payments/admin-action/",
                telegram_id=telegram_id,
                params={"is_admin": "true"},
                json={
                    "payment_id": payment_id,
                    "admin_id": str(telegram_id),
                    "action": "cancel"
                }
            )
            
            if result:
                logger.info(f"Payment {payment_id} cancelled successfully")
                return True
            
            # Second approach: Try a PUT request to update the payment status
            logger.info(f"First approach failed. Trying to update payment via PUT")
            result = await self.make_request(
                "PUT",
                f"{self.base_url}/payments/admin-update/",
                telegram_id=telegram_id,
                params={"is_admin": "true"},
                json={
                    "payment_id": payment_id,
                    "admin_id": str(telegram_id),
                    "status": "cancelled"
                }
            )
            
            if result:
                logger.info(f"Payment {payment_id} cancelled successfully with PUT")
                return True
            
            logger.error(f"Failed to cancel payment {payment_id}")
            return False
        except Exception as e:
            logger.error(f"Error cancelling payment {payment_id}: {e}")
            return False

    async def get_student_by_telegram_id(self, telegram_id: str) -> Optional[Dict]:
        """Get student details by Telegram ID"""
        try:
            logger.info(f"Getting student data for telegram_id {telegram_id}")
            result = await self.make_request(
                "GET", 
                f"{self.base_url}/students/", 
                params={"telegram_id": telegram_id}
            )
            
            if result and isinstance(result, list) and len(result) > 0:
                student = result[0]
                logger.info(f"Found student: {student['name']} ({student['telegram_id']})")
                self._register_user(int(telegram_id))
                return student
            else:
                logger.warning(f"No student found with telegram_id {telegram_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting student by telegram_id {telegram_id}: {e}")
            return None

    async def register_user(self, telegram_id: int, name: str = None) -> bool:
        """Register a user in the system"""
        if not telegram_id:
            logger.error("Missing telegram_id for user registration")
            return False
        
        try:
            # This is essentially the same as ensure_user_exists but with a different name
            # for clarity in the code
            result = await self.ensure_user_exists(telegram_id=telegram_id, name=name)
            return result
        except Exception as e:
            logger.error(f"Error registering user {telegram_id}: {e}")
            return False

    async def ensure_session_closed(self):
        """Ensure the session is closed properly"""
        if self._session and not self._session.closed:
            try:
                await self._session.close()
                logger.info("API client session closed")
            except Exception as e:
                logger.error(f"Error closing API client session: {e}")

    async def get_pending_payment(self, telegram_id: int, course_id: int) -> Optional[Dict[str, Any]]:
        """Check if there's an existing pending payment for a user and course"""
        try:
            logger.info(f"Checking for pending payments for user {telegram_id}, course {course_id}")
            result = await self.make_request(
                "GET",
                f"{self.base_url}/payments/",
                params={
                    "telegram_id": telegram_id,
                    "course": course_id,
                    "status": "pending"
                }
            )
            
            if result and isinstance(result, list) and len(result) > 0:
                logger.info(f"Found pending payment {result[0]['id']} for user {telegram_id}, course {course_id}")
                return result[0]
            
            logger.info(f"No pending payments found for user {telegram_id}, course {course_id}")
            return None
        except Exception as e:
            logger.error(f"Error checking pending payments: {e}")
            return None

    async def is_valid_telegram_user(self, telegram_id: int) -> bool:
        """
        Check if a telegram_id represents a valid user who can receive messages.
        Warning: This is a best-effort check and may not be 100% accurate.
        """
        # Basic validation for test accounts or obviously invalid IDs
        if not telegram_id or int(telegram_id) < 10000:
            logger.warning(f"Telegram ID {telegram_id} appears to be invalid (too small)")
            return False
        
        # Check if the user exists in our system
        user_info = await self.make_request(
            "GET",
            f"{self.base_url}/students/",
            params={"telegram_id": telegram_id}
        )
        
        if not user_info or not isinstance(user_info, list) or len(user_info) == 0:
            logger.warning(f"User with telegram_id {telegram_id} not found in database")
            return False
        
        # Unfortunately, we can't reliably check if a user has blocked the bot or never
        # started it without actually trying to send a message.
        return True
