from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

import config


engine = create_engine(config.DATABASE_URL, poolclass=NullPool)
session_maker = sessionmaker(engine, expire_on_commit=False)


def get_session():
    """
    Create async session for work with database
    :return: AsyncSession
    """
    with session_maker() as session:
        yield session


def init_models() -> None:
    from dbmodels import DBCountry  # noqa: unused
    from dbmodels import DBUser  # noqa: unused
    with engine.begin() as conn:
        SQLModel.metadata.create_all(conn)
