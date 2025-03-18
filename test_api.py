#!/usr/bin/env python
import asyncio

import aiohttp


async def test_api():
    async with aiohttp.ClientSession() as session:
        # Test payments endpoint with telegram_id
        print("Testing payments endpoint with telegram_id:")
        async with session.get('http://localhost:8000/api/payments/?telegram_id=123456&status=confirmed') as response:
            print(f'Status: {response.status}')
            print(f'Content: {await response.text()}')
            print()
        
        # Test mentors endpoint (should be public)
        print("Testing mentors endpoint (public):")
        async with session.get('http://localhost:8000/api/mentors/') as response:
            print(f'Status: {response.status}')
            content = await response.text()
            print(f'Content length: {len(content)} characters')
            print()
        
        # Test student registration
        print("Testing student registration:")
        student_data = {
            'telegram_id': '999888',
            'name': 'Test User'
        }
        async with session.post('http://localhost:8000/api/students/register/', json=student_data) as response:
            print(f'Status: {response.status}')
            print(f'Content: {await response.text()}')
            print()
            
        # Test student lookup
        print("Testing student lookup by telegram_id:")
        async with session.get('http://localhost:8000/api/students/?telegram_id=999888') as response:
            print(f'Status: {response.status}')
            print(f'Content: {await response.text()}')

if __name__ == "__main__":
    asyncio.run(test_api()) 