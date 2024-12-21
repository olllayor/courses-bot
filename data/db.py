# datas/db.py
from data.api_client import APIClient
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)
api_client = APIClient()

async def fetch_mentors(telegram_id: int = None) -> List[str]:
    """
    Fetch mentor names from the API.
    
    Args:
        telegram_id: Optional telegram ID for filtering
        
    Returns:
        List of mentor names
    """
    try:
        api_client = APIClient()
        mentors = await api_client.get_mentors()
        return [mentor["name"] for mentor in mentors if mentor.get("name")]
    except Exception as e:
        logger.error(f"Error fetching mentors: {e}")
        return []

async def fetch_mentor_details(mentor_name: str) -> Optional[Dict]:
    """
    Fetches detailed information about a mentor by name.
    """
    try:
        return await api_client.get_mentor_by_name(mentor_name)
    except Exception as e:
        print(f"Error fetching mentor details: {e}")
        return None

async def show_mentor_availability(mentor_id: int) -> Optional[List[Dict]]:
    try:
        return await api_client.get_mentor_availability(mentor_id)
    except Exception as e:
        print(f"Error fetching mentor availability: {e}")
        return None