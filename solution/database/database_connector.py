from sqlalchemy import NullPool
from sqlmodel import create_engine, Session
from sqlmodel import SQLModel

import config


engine = create_engine(config.DATABASE_URL, poolclass=NullPool, echo=True)


def get_session():
    """
    Create async session for work with database
    :return: AsyncSession
    """
    with Session(engine) as session:
        yield session


def init_models() -> None:
    from dbmodels import DBCountry  # noqa: unused
    from dbmodels import DBUser  # noqa: unused
    with engine.begin() as conn:
        SQLModel.metadata.create_all(conn)
