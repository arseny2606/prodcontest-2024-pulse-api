from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, conint, constr, RootModel


class PingResponse(BaseModel):
    status: str


class CountryRegion(Enum):
    Europe = 'Europe'
    Africa = 'Africa'
    Americas = 'Americas'
    Oceania = 'Oceania'
    Asia = 'Asia'


class CountryAlpha2(RootModel[str]):
    root: constr(pattern=r'[a-zA-Z]{2}', max_length=2) = Field(
        ...,
        description='Двухбуквенный код, уникально идентифицирующий страну',
        example='RU',
    )


class Country(BaseModel):
    name: constr(max_length=100) = Field(..., description='Полное название страны')
    alpha2: CountryAlpha2
    alpha3: constr(pattern=r'[a-zA-Z]{3}', max_length=3) = Field(
        ..., description='Трехбуквенный код страны'
    )
    region: Optional[str] = None


class UserLogin(RootModel[str]):
    root: constr(pattern=r'[a-zA-Z0-9-]+', max_length=30) = Field(
        ..., description='Логин пользователя', example='yellowMonkey'
    )


class UserEmail(RootModel[str]):
    root: constr(min_length=1, max_length=50) = Field(
        ..., description='E-mail пользователя', example='yellowstone1980@you.ru'
    )


class UserPassword(RootModel[str]):
    root: constr(min_length=6, max_length=100) = Field(
        ...,
        description='Пароль пользователя, к которому предъявляются следующие требования:\n\n- Длина пароля не менее 6 '
                    'символов.\n- Присутствуют латинские символы в нижнем и верхнем регистре.\n- Присутствует минимум '
                    'одна цифра.\n',
        example='$aba4821FWfew01#.fewA$',
    )


class UserIsPublic(RootModel[bool]):
    root: bool = Field(
        ...,
        description='Является ли данный профиль публичным. \n\nПубличные профили доступны другим пользователям: если '
                    'профиль публичный, любой пользователь платформы сможет получить информацию о пользователе.\n',
        example=True,
    )


class UserPhone(RootModel[str]):
    root: constr(min_length=1, pattern=r'\+[\d]+') = Field(
        ...,
        description='Номер телефона пользователя в формате +123456789',
        example='+74951239922',
    )


class UserImage(RootModel[str]):
    root: constr(min_length=1, max_length=200) = Field(
        ...,
        description='Ссылка на фото для аватара пользователя',
        example='https://http.cat/images/100.jpg',
    )


class UserProfile(BaseModel):
    login: UserLogin
    email: UserEmail
    countryCode: CountryAlpha2
    isPublic: UserIsPublic
    phone: Optional[UserPhone] = None
    image: Optional[UserImage] = None


class PostId(RootModel[str]):
    root: constr(max_length=100) = Field(
        ...,
        description='Уникальный идентификатор публикации, присвоенный сервером.',
        example='550e8400-e29b-41d4-a716-446655440000',
    )


class PostContent(RootModel[str]):
    root: constr(max_length=1000) = Field(
        ...,
        description='Текст публикации.',
        example='Свеча на 400! Покупаем, докупаем и фиксируем прибыль.',
    )


class PostTags(RootModel[str]):
    root: List[constr(max_length=20)] = Field(
        ...,
        description='Список тегов публикации.',
        example=['тинькофф', 'спббиржа', 'moex'],
    )


class Post(BaseModel):
    id: PostId
    content: PostContent
    author: UserLogin
    tags: PostTags
    createdAt: str = Field(
        ...,
        description='Серверная дата и время в момент, когда пользователь отправил данную публикацию.\nПередается в '
                    'формате RFC3339.\n',
        example='2006-01-02T15:04:05Z07:00',
    )
    likesCount: conint(ge=0) = Field(
        ..., description='Число лайков, набранное публикацией.'
    )
    dislikesCount: conint(ge=0) = Field(
        ..., description='Число дизлайков, набранное публикацией.'
    )


class ErrorResponse(BaseModel):
    reason: constr(min_length=5) = Field(
        ..., description='Описание ошибки в свободной форме'
    )


class AuthRegisterPostRequest(BaseModel):
    login: UserLogin
    email: UserEmail
    password: UserPassword
    countryCode: CountryAlpha2
    isPublic: UserIsPublic
    phone: Optional[UserPhone] = None
    image: Optional[UserImage] = None


class AuthRegisterPostResponse(BaseModel):
    profile: UserProfile


class AuthSignInPostRequest(BaseModel):
    login: UserLogin
    password: UserPassword


class AuthSignInPostResponse(BaseModel):
    token: constr(min_length=20) = Field(
        ...,
        description='Сгенерированный токен пользователя',
        example='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9'
                '.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ'
                '.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c',
    )


class MeProfilePatchRequest(BaseModel):
    countryCode: Optional[CountryAlpha2] = None
    isPublic: Optional[UserIsPublic] = None
    phone: Optional[UserPhone] = None
    image: Optional[UserImage] = None


class MeUpdatePasswordPostRequest(BaseModel):
    oldPassword: UserPassword
    newPassword: UserPassword


class MeUpdatePasswordPostResponse(BaseModel):
    status: str = Field(
        ..., description='Должно принимать значение `ok`.', example='ok'
    )


class FriendsAddPostRequest(BaseModel):
    login: UserLogin


class FriendsAddPostResponse(BaseModel):
    status: str = Field(
        ..., description='Должно принимать значение `ok`.', example='ok'
    )


class FriendsRemovePostRequest(BaseModel):
    login: UserLogin


class FriendsRemovePostResponse(BaseModel):
    status: str = Field(
        ..., description='Должно принимать значение `ok`.', example='ok'
    )


class FriendsGetResponse(BaseModel):
    login: UserLogin
    addedAt: str = Field(
        ...,
        description='Время и дата, когда данный пользователь был добавлен в друзья в последний раз.\n\nПередается в '
                    'формате RFC3339.\n',
        example='2006-01-02T15:04:05Z07:00',
    )


class PostsNewPostRequest(BaseModel):
    content: PostContent
    tags: PostTags
