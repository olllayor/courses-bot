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