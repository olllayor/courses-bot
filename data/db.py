# datas/db.py
from data.api_client import APIClient
from typing import List, Dict, Optional

api_client = APIClient()

async def show_mentors() -> List[str]:
    try:
        mentors = await api_client.get_mentors()
        return [mentor['name'] for mentor in mentors]
    except Exception as e:
        print(f"Error fetching mentors: {e}")
        return []

async def get_mentor_info(mentor_name: str) -> Optional[Dict]:
    try:
        return await api_client.get_mentor_by_name(mentor_name)
    except Exception as e:
        print(f"Error fetching mentor info: {e}")
        return None

async def show_mentor_availability(mentor_id: int) -> Optional[List[Dict]]:
    try:
        return await api_client.get_mentor_availability(mentor_id)
    except Exception as e:
        print(f"Error fetching mentor availability: {e}")
        return None