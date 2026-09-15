import asyncio, json, asyncpg
async def main():
 conn = await asyncpg.connect('postgresql://tripmate:tripmate@localhost:5432/tripmate')
 val = await conn.fetchval("SELECT travel_state FROM threads ORDER BY created_at DESC LIMIT 1")
 with open('state_new.txt', 'w', encoding='utf-8') as f:
  f.write(val)
 await conn.close()
asyncio.run(main())
