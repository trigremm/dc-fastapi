from sqlalchemy.ext.asyncio import async_sessionmaker

from app.database.engines import engine

async_session = async_sessionmaker(engine, expire_on_commit=False)
