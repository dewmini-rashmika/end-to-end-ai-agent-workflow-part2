import asyncio, json, asyncpg
async def main():
 conn = await asyncpg.connect('postgresql://tripmate:tripmate@localhost:5432/tripmate')
 val = await conn.fetchval("SELECT travel_state FROM threads WHERE id = '372cad7e-4310-447f-baee-176e786c8dd8'")
 with open('state.txt', 'w', encoding='utf-8') as f:
  f.write(val)
 await conn.close()
asyncio.run(main())
