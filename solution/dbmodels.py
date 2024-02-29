import datetime
from typing import Optional

from pydantic import constr
from sqlalchemy import event
from sqlmodel import Field, SQLModel


class DBCountry(SQLModel, table=True):
    __tablename__ = "countries"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: constr(max_length=100)
    alpha2: constr(pattern=r'[a-zA-Z]{2}', max_length=2)
    alpha3: constr(pattern=r'[a-zA-Z]{3}', max_length=3)
    region: str


class DBUser(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    login: constr(pattern=r'[a-zA-Z0-9-]+', max_length=30) = Field(unique=True)
    password: constr(min_length=6)
    email: constr(max_length=50) = Field(unique=True)
    countryCode: constr(pattern=r'[a-zA-Z]{2}', max_length=2)
    isPublic: bool
    phone: constr(pattern=r'\+[\d]+') = Field(unique=True, nullable=True)
    image: constr(max_length=200) = Field(nullable=True)
    updated_at: int = Field(nullable=True)


@event.listens_for(DBUser, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.updated_at = int(datetime.datetime.now().timestamp())
