#!/bin/sh
set -e

echo "Starting Udemy Free Deals..."
echo "Running database migrations..."
python -c "
from app.database import Base, engine
import asyncio
async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
asyncio.run(init())
print('Database tables created/verified.')
"

echo "Starting server on port 8080..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8080
