from typing import List, Optional, Union, Annotated

from fastapi import FastAPI, APIRouter, Depends, Query
from pydantic import conint
from sqlalchemy.orm import Session

from database.database_connector import init_models, get_session
from dbmodels import DBCountry
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

init_models()

app = FastAPI(
    title='Pulse API',
    version='1.0',
)

router = APIRouter(prefix="/api")


@router.post(
    '/auth/register',
    response_model=None,
    responses={
        '201': {'model': AuthRegisterPostResponse},
        '400': {'model': ErrorResponse},
        '409': {'model': ErrorResponse},
    },
)
def auth_register(
        body: AuthRegisterPostRequest,
) -> Union[None, AuthRegisterPostResponse, ErrorResponse]:
    """
    Регистрация нового пользователя
    """
    pass


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


@router.get('/countries', response_model=List[Country])
def list_countries(region: Optional[List[str]] = Query(None), db_session: Session = Depends(get_session)) \
        -> list[Country]:
    """
    Получить список стран
    """
    stmt = db_session.query(DBCountry)
    if region:
        stmt = stmt.filter(DBCountry.region.in_(region))
    return stmt.all()


@router.get(
    '/countries/{alpha2}',
    response_model=DBCountry,
    responses={'404': {'model': ErrorResponse}},
)
def get_country(alpha2: Annotated[str, CountryAlpha2]) -> Union[DBCountry, ErrorResponse]:
    """
    Получить страну по alpha2 коду
    """
    pass


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
