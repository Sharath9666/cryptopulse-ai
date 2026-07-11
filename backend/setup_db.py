import asyncio
import asyncpg

async def setup():
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="Sharath@1234",
        database="postgres"
    )
    dbs = await conn.fetch("SELECT datname FROM pg_database WHERE datname = 'cryptopulse'")
    if not dbs:
        await conn.execute("CREATE DATABASE cryptopulse")
        print("Created database: cryptopulse")
    else:
        print("Database cryptopulse already exists")
    await conn.close()

asyncio.run(setup())
