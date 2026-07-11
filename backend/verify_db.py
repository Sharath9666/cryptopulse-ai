import asyncio
import asyncpg

async def verify():
    conn = await asyncpg.connect(
        host="localhost", port=5432,
        user="postgres", password="Sharath@1234",
        database="cryptopulse"
    )
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    )
    print("Tables in cryptopulse DB:")
    for t in tables:
        tname = t["tablename"]
        cnt = await conn.fetchval(f"SELECT COUNT(*) FROM {tname}")
        print(f"  {tname:30s} -> {cnt} rows")
    await conn.close()

asyncio.run(verify())
