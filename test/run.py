from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.llm_client import send_to_llm
import asyncio

async def main():
    response = await send_to_llm('Who are you')
    print(response)

if __name__ == '__main__':
    asyncio.run(main())