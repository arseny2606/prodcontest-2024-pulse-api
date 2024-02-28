from typing import List, Optional, Union, Annotated

from fastapi import FastAPI, APIRouter, Depends, Query, Response
from fastapi.exceptions import RequestValidationError
from passlib.context import CryptContext
from pydantic import conint
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from database.database_connector import init_models, get_session
from dbmodels import DBCountry, DBUser
from models import (
    AuthRegisterPostRequest,
    AuthRegisterPostResponse,
    AuthSignInPostResponse,
    CountryAlpha2,
    ErrorResponse,
    FriendsAddPostRequest,
    FriendsAddPostResponse,
    FriendsGetResponse,
    FriendsRemovePostRequest,
    FriendsRemovePostResponse,
    MeProfilePatchRequest,
    MeUpdatePasswordPostRequest,
    MeUpdatePasswordPostResponse,
    Post,
    PostId,
    PostsNewPostRequest,
    UserLogin,
    UserProfile, PingResponse, Country,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


init_models()

app = FastAPI(
    title='Pulse API',
    version='1.0',
)

router = APIRouter(prefix="/api")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"reason": str(exc)})


@router.post(
    '/auth/register',
    response_model=Union[AuthRegisterPostResponse, ErrorResponse],
    responses={
        '201': {'model': AuthRegisterPostResponse},
        '400': {'model': ErrorResponse},
        '409': {'model': ErrorResponse},
    },
    response_model_exclude_none=True,
)
def auth_register(
        response: Response, body: AuthRegisterPostRequest, db_session: Session = Depends(get_session)
) -> Union[AuthRegisterPostResponse, ErrorResponse]:
    """
    Регистрация нового пользователя
    """
    db_model = DBUser(**body.dict())
    if not all([any([i for i in db_model.password if i.islower()]), any([i for i in db_model.password if i.isupper()]),
                any([i for i in db_model.password if i.isdigit()])]):
        response.status_code = 400
        return ErrorResponse(reason="invalid password")
    db_model.password = get_password_hash(db_model.password)
    country = db_session.query(DBCountry).filter(DBCountry.alpha2 == db_model.countryCode)
    if not country.first():
        response.status_code = 400
        return ErrorResponse(reason="no such country")
    db_session.add(db_model)
    try:
        db_session.commit()
    except:
        response.status_code = 409
        return ErrorResponse(reason="conflict")
    response.status_code = 201
    return AuthRegisterPostResponse(profile=UserProfile(**db_model.dict(exclude_none=True)))


@router.post(
    '/auth/sign-in',
    response_model=AuthSignInPostResponse,
    responses={'401': {'model': ErrorResponse}},
)
def auth_sign_in() -> Union[AuthSignInPostResponse, ErrorResponse]:
    """
    Аутентификация для получения токена
    """
    pass


@router.get('/countries', response_model=Union[List[Country], ErrorResponse])
def list_countries(response: Response, region: Optional[List[str]] = Query(None),
                   db_session: Session = Depends(get_session)) \
        -> Union[list[Country], ErrorResponse]:
    """
    Получить список стран
    """
    stmt = db_session.query(DBCountry).order_by(DBCountry.alpha2.asc())
    if region:
        stmt = stmt.filter(DBCountry.region.in_(region))
    countries = stmt.all()
    if countries:
        return countries
    if region:
        response.status_code = 400
        return ErrorResponse(reason="no filtered countries")
    return []


@router.get(
    '/countries/{alpha2}',
    response_model=Union[Country, ErrorResponse],
    responses={404: {'model': ErrorResponse}},
)
def get_country(response: Response, alpha2: Annotated[str, CountryAlpha2], db_session: Session = Depends(get_session)) \
        -> Union[Country, ErrorResponse]:
    """
    Получить страну по alpha2 коду
    """
    stmt = db_session.query(DBCountry).filter(DBCountry.alpha2 == alpha2.root)
    country = stmt.first()
    if country is None:
        response.status_code = 404
        return ErrorResponse(reason="country not found")
    return country


@router.get(
    '/friends',
    response_model=List[FriendsGetResponse],
    responses={'401': {'model': ErrorResponse}},
)
def friends_list(
        limit: Optional[conint(ge=0, le=50)] = 5, offset: Optional[int] = 0
) -> Union[List[FriendsGetResponse], ErrorResponse]:
    """
    Получение списка друзей
    """
    pass


@router.post(
    '/friends/add',
    response_model=FriendsAddPostResponse,
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def friends_add(
        body: FriendsAddPostRequest,
) -> Union[FriendsAddPostResponse, ErrorResponse]:
    """
    Добавить пользователя в друзья
    """
    pass


@router.post(
    '/friends/remove',
    response_model=FriendsRemovePostResponse,
    responses={'401': {'model': ErrorResponse}},
)
def friends_remove(
        body: FriendsRemovePostRequest,
) -> Union[FriendsRemovePostResponse, ErrorResponse]:
    """
    Удалить пользователя из друзей
    """
    pass


@router.get(
    '/me/profile',
    response_model=UserProfile,
    responses={'401': {'model': ErrorResponse}},
)
def get_my_profile() -> Union[UserProfile, ErrorResponse]:
    """
    Получение собственного профиля
    """
    pass


@router.patch(
    '/me/profile',
    response_model=UserProfile,
    responses={'401': {'model': ErrorResponse}},
)
def patch_my_profile(body: MeProfilePatchRequest) -> Union[UserProfile, ErrorResponse]:
    """
    Редактирование собственного профиля
    """
    pass


@router.post(
    '/me/updatePassword',
    response_model=MeUpdatePasswordPostResponse,
    responses={
        '400': {'model': ErrorResponse},
        '401': {'model': ErrorResponse},
        '403': {'model': ErrorResponse},
    },
)
def update_password(
        body: MeUpdatePasswordPostRequest,
) -> Union[MeUpdatePasswordPostResponse, ErrorResponse]:
    """
    Обновление пароля
    """
    pass


@router.get('/ping', response_model=PingResponse)
def ping() -> Union[PingResponse, ErrorResponse]:
    """
    Проверка сервера на готовность принимать запросы
    """
    return PingResponse(status="ok")


@router.get(
    '/posts/feed/my', response_model=Post, responses={'401': {'model': ErrorResponse}}
)
def get_my_feed(
        limit: Optional[conint(ge=0, le=50)] = 5, offset: Optional[int] = 0
) -> Union[Post, ErrorResponse]:
    """
    Получить ленту со своими постами
    """
    pass


@router.get(
    '/posts/feed/{login}',
    response_model=Post,
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def get_feed_by_others(
        login: Annotated[str, UserLogin],
        limit: Optional[conint(ge=0, le=50)] = 5,
        offset: Optional[int] = 0,
) -> Union[Post, ErrorResponse]:
    """
    Получить ленту с постами другого пользователя
    """
    pass


@router.post(
    '/posts/new', response_model=Post, responses={'401': {'model': ErrorResponse}}
)
def submit_post(body: PostsNewPostRequest) -> Union[Post, ErrorResponse]:
    """
    Отправить публикацию
    """
    pass


@router.get(
    '/posts/{post_id}',
    response_model=Post,
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def get_post_by_id(
        post_id: Annotated[str, PostId]
) -> Union[Post, ErrorResponse]:
    """
    Получить ленту со своими постами
    """
    pass


@router.post(
    '/posts/{post_id}/dislike',
    response_model=Post,
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def dislike_post(
        post_id: Annotated[str, PostId]
) -> Union[Post, ErrorResponse]:
    """
    Дизлайк поста
    """
    pass


@router.post(
    '/posts/{post_id}/like',
    response_model=Post,
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def like_post(
        post_id: Annotated[str, PostId]
) -> Union[Post, ErrorResponse]:
    """
    Лайк поста
    """
    pass


@router.get(
    '/profiles/{login}',
    response_model=UserProfile,
    responses={'401': {'model': ErrorResponse}, '403': {'model': ErrorResponse}},
)
def get_profile(login: Annotated[str, UserLogin]) -> Union[UserProfile, ErrorResponse]:
    """
    Получение профиля пользователя по логину
    """
    pass


app.include_router(router)
