import datetime
import uuid
from typing import Optional

from pydantic import constr
from sqlalchemy import event, UniqueConstraint, Table, Column, Integer, ForeignKey, DateTime, func, UUID, String
from sqlmodel import Field, SQLModel, Relationship


class DBCountry(SQLModel, table=True):
    __tablename__ = "countries"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: constr(max_length=100)
    alpha2: constr(pattern=r'[a-zA-Z]{2}', max_length=2)
    alpha3: constr(pattern=r'[a-zA-Z]{3}', max_length=3)
    region: str


friends = Table(
    "friends",
    SQLModel.metadata,
    Column("whoadded_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("added_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("added_at", DateTime, nullable=False, default=func.now()),
    UniqueConstraint('whoadded_id', 'added_id', name='_friends_uc'),
)


class DBUser(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    login: constr(pattern=r'[a-zA-Z0-9-]+', max_length=30) = Field(unique=True)
    password: constr(min_length=6)
    email: constr(max_length=50) = Field(unique=True)
    countryCode: constr(pattern=r'[a-zA-Z]{2}', max_length=2)
    isPublic: bool
    phone: constr(pattern=r'\+[\d]+', max_length=20) = Field(unique=True, nullable=True)
    image: constr(max_length=200) = Field(nullable=True)
    updated_at: float = Field(nullable=True)

    friends: list["DBUser"] = Relationship(sa_relationship_kwargs={"secondary": "friends",
                                                                   "order_by": "friends.c.added_at",
                                                                   "primaryjoin": "DBUser.id==friends.c.whoadded_id",
                                                                   "secondaryjoin": "DBUser.id==friends.c.added_id",
                                                                   "backref": "added_to_friends",
                                                                   "lazy": "dynamic"})
    posts: list["DBPost"] = Relationship(back_populates="owner")


@event.listens_for(DBUser, 'before_insert')
def receive_before_insert(mapper, connection, target):
    target.updated_at = datetime.datetime.now().timestamp()


class DBTag(SQLModel, table=True):
    __tablename__ = "tags"

    tag: constr(max_length=20) = Field(primary_key=True)
    post_id: uuid.UUID = Field(sa_column=Column(UUID(as_uuid=True), ForeignKey("posts.id"), primary_key=True))

    post: "DBPost" = Relationship(back_populates="tags")
    __table_args__ = UniqueConstraint('post_id', 'tag', name='_tags_uc'),


class DBPost(SQLModel, table=True):
    __tablename__ = "posts"

    id: Optional[uuid.UUID] = Field(sa_column=Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4))
    content: constr(max_length=1000)
    owner_id: int = Field(foreign_key="users.id")
    createdAt: Optional[datetime.datetime] = Field(nullable=False, default=func.now())

    tags: list[DBTag] = Relationship()
    owner: DBUser = Relationship()
