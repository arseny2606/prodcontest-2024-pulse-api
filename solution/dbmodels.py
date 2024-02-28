from typing import Optional

from sqlmodel import Field, SQLModel
from pydantic import constr


class DBCountry(SQLModel, table=True):
    __tablename__ = "countries"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: constr(max_length=100)
    alpha2: constr(pattern=r'[a-zA-Z]{2}', max_length=2)
    alpha3: constr(pattern=r'[a-zA-Z]{3}', max_length=3)
    region: str
