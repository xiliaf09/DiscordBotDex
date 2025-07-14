import httpx
import json
import asyncio

async def test_clanker_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://www.clanker.world/api/tokens", params={"page": 1, "sort": "desc"})
        data = response.json()
        print(json.dumps(data, indent=2))

if __name__ == "__main__":
    asyncio.run(test_clanker_api()) 