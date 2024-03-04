import datetime
import uuid
from typing import List, Optional, Union, Annotated

import rfc3339
from fastapi import FastAPI, APIRouter, Depends, Query, Response
from fastapi.exceptions import HTTPException, RequestValidationError
from passlib.context import CryptContext
from pydantic import conint
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from auth import create_access_token, get_current_user
from database.database_connector import init_models, get_session
from dbmodels import DBCountry, DBUser, friends, DBPost, DBTag, post_rates
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
    UserProfile, PingResponse, Country, AuthSignInPostRequest, CountryRegion,
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
async def exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"reason": str(exc)})


@app.exception_handler(HTTPException)
async def exception_handler(request, exc):
    if exc.status_code == 401:
        return JSONResponse(status_code=401, content={"reason": str(exc.detail)})
    if exc.status_code >= 500:
        return JSONResponse(status_code=exc.status_code, content={"reason": str(exc.detail)})
    return JSONResponse(status_code=400, content={"reason": str(exc.detail)})


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
    if db_model.login == "my":
        response.status_code = 400
        return ErrorResponse(reason="invalid login")
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
    response_model=Union[AuthSignInPostResponse, ErrorResponse],
    responses={'401': {'model': ErrorResponse}},
)
def auth_sign_in(response: Response, body: AuthSignInPostRequest, db_session: Session = Depends(get_session)) -> Union[
    AuthSignInPostResponse, ErrorResponse]:
    """
    Аутентификация для получения токена
    """
    user = db_session.query(DBUser).filter(DBUser.login == body.login.root).first()
    if user is None or not verify_password(body.password.root, user.password):
        response.status_code = 401
        return ErrorResponse(reason="user not found")
    token = create_access_token({"login": user.login})
    return AuthSignInPostResponse(token=token)


@router.get('/countries', response_model=Union[List[Country], ErrorResponse])
def list_countries(response: Response, region: Optional[List[CountryRegion]] = Query(None),
                   db_session: Session = Depends(get_session)) \
        -> Union[list[Country], ErrorResponse]:
    """
    Получить список стран
    """
    stmt = db_session.query(DBCountry).order_by(DBCountry.alpha2.asc())
    if region:
        stmt = stmt.filter(DBCountry.region.in_([i.value for i in region]))
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
        limit: Optional[conint(ge=0, le=50)] = 5, offset: Optional[conint(ge=0)] = 0, current_user=Depends(get_current_user),
        db_session: Session = Depends(get_session)
) -> Union[List[FriendsGetResponse], ErrorResponse]:
    """
    Получение списка друзей
    """
    added_at_get = select(friends.c.added_id, friends.c.added_at).where(friends.c.whoadded_id == current_user.id)
    added_at_res = db_session.execute(added_at_get).all()
    added_at_dict = {i[0]: i[1] for i in added_at_res}
    return [FriendsGetResponse(login=friend.login, addedAt=rfc3339.rfc3339(added_at_dict[friend.id])) for friend in
            current_user.friends[offset:offset + limit]]


@router.post(
    '/friends/add',
    response_model=Union[FriendsAddPostResponse, ErrorResponse],
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def friends_add(
        response: Response, body: FriendsAddPostRequest, current_user=Depends(get_current_user),
        db_session=Depends(get_session)
) -> Union[FriendsAddPostResponse, ErrorResponse]:
    """
    Добавить пользователя в друзья
    """
    if body.login.root == current_user.login:
        return FriendsAddPostResponse(status="ok")
    user_to_add = db_session.query(DBUser).where(DBUser.login == body.login.root).first()
    if user_to_add is None:
        response.status_code = 404
        return ErrorResponse(reason="user not found")
    current_user.friends.append(user_to_add)
    db_session.add(current_user)
    try:
        db_session.commit()
    except:
        pass
    return FriendsAddPostResponse(status="ok")


@router.post(
    '/friends/remove',
    response_model=FriendsRemovePostResponse,
    responses={'401': {'model': ErrorResponse}},
)
def friends_remove(
        body: FriendsRemovePostRequest, current_user=Depends(get_current_user),
        db_session=Depends(get_session)
) -> Union[FriendsRemovePostResponse, ErrorResponse]:
    """
    Удалить пользователя из друзей
    """
    user_to_add = db_session.query(DBUser).where(DBUser.login == body.login.root).first()
    if user_to_add is None:
        return FriendsRemovePostResponse(status="ok")
    current_user.friends = [friend for friend in current_user.friends if friend.id != user_to_add.id]
    db_session.add(current_user)
    try:
        db_session.commit()
    except:
        pass
    return FriendsRemovePostResponse(status="ok")


@router.get(
    '/me/profile',
    response_model=UserProfile,
    response_model_exclude_none=True,
    responses={'401': {'model': ErrorResponse}},
)
def get_my_profile(current_user=Depends(get_current_user)) -> Union[UserProfile, ErrorResponse]:
    """
    Получение собственного профиля
    """
    return current_user


@router.patch(
    '/me/profile',
    response_model=Union[UserProfile, ErrorResponse],
    response_model_exclude_none=True,
    responses={'401': {'model': ErrorResponse}, '409': {'model': ErrorResponse}},
)
def patch_my_profile(response: Response, body: MeProfilePatchRequest, current_user=Depends(get_current_user),
                     db_session: Session = Depends(get_session)) -> Union[UserProfile, ErrorResponse]:
    """
    Редактирование собственного профиля
    """
    body_without_none = body.dict(exclude_none=True)
    if not body_without_none:
        response.status_code = 400
        return ErrorResponse(reason="no fields")
    for key in body_without_none:
        setattr(current_user, key, body_without_none[key])
    if body_without_none.get("countryCode"):
        country = db_session.query(DBCountry).filter(DBCountry.alpha2 == body_without_none.get("countryCode"))
        if not country.first():
            response.status_code = 400
            return ErrorResponse(reason="no such country")
    db_session.add(current_user)
    try:
        db_session.commit()
    except:
        response.status_code = 409
        return ErrorResponse(reason="conflict")
    return current_user


@router.post(
    '/me/updatePassword',
    response_model=Union[MeUpdatePasswordPostResponse, ErrorResponse],
    responses={
        '400': {'model': ErrorResponse},
        '401': {'model': ErrorResponse},
        '403': {'model': ErrorResponse},
    },
)
def update_password(
        response: Response, body: MeUpdatePasswordPostRequest, current_user=Depends(get_current_user),
        db_session=Depends(get_session)
) -> Union[MeUpdatePasswordPostResponse, ErrorResponse]:
    """
    Обновление пароля
    """
    if not all([any([i for i in body.newPassword.root if i.islower()]),
                any([i for i in body.newPassword.root if i.isupper()]),
                any([i for i in body.newPassword.root if i.isdigit()])]):
        response.status_code = 400
        return ErrorResponse(reason="invalid password")
    if not verify_password(body.oldPassword.root, current_user.password):
        response.status_code = 403
        return ErrorResponse(reason="invalid old password")
    current_user.password = get_password_hash(body.newPassword.root)
    current_user.updated_at = datetime.datetime.now().timestamp()
    db_session.add(current_user)
    db_session.commit()
    return MeUpdatePasswordPostResponse(status="ok")


@router.get('/ping', response_model=PingResponse)
def ping() -> Union[PingResponse, ErrorResponse]:
    """
    Проверка сервера на готовность принимать запросы
    """
    return PingResponse(status="ok")


@router.get(
    '/posts/feed/my', response_model=List[Post], responses={'401': {'model': ErrorResponse}}
)
def get_my_feed(
        limit: Optional[conint(ge=0, le=50)] = 5, offset: Optional[conint(ge=0)] = 0, current_user=Depends(get_current_user)
) -> Union[List[Post], ErrorResponse]:
    """
    Получить ленту со своими постами
    """
    return [Post(id=str(post.id), content=post.content,
                 author=post.owner.login, createdAt=rfc3339.rfc3339(post.createdAt),
                 tags=[tag.tag for tag in post.tags], likesCount=post.liked_users.count(),
                 dislikesCount=post.disliked_users.count()) for post in
            current_user.posts[offset:offset + limit]]


@router.get(
    '/posts/feed/{login}',
    response_model=Union[List[Post], ErrorResponse],
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def get_feed_by_others(
        response: Response,
        login: Annotated[str, UserLogin],
        limit: Optional[conint(ge=0, le=50)] = 5,
        offset: Optional[conint(ge=0)] = 0,
        current_user=Depends(get_current_user),
        db_session=Depends(get_session)
) -> Union[List[Post], ErrorResponse]:
    """
    Получить ленту с постами другого пользователя
    """
    user = db_session.query(DBUser).where(DBUser.login == login.root).first()  # noqa
    if not user or (not user.isPublic and user != current_user and current_user not in user.friends):
        response.status_code = 404
        return ErrorResponse(reason="posts not found")
    return [Post(id=str(post.id), content=post.content,
                 author=post.owner.login, createdAt=rfc3339.rfc3339(post.createdAt),
                 tags=[tag.tag for tag in post.tags], likesCount=post.liked_users.count(),
                 dislikesCount=post.disliked_users.count()) for post in
            user.posts[offset:offset + limit]]


@router.post(
    '/posts/new', response_model=Post, responses={'401': {'model': ErrorResponse}}
)
def submit_post(body: PostsNewPostRequest, current_user=Depends(get_current_user), db_session=Depends(get_session)) -> \
        Union[Post, ErrorResponse]:
    """
    Отправить публикацию
    """
    new_post = DBPost(content=body.content.root, tags=[DBTag(tag=tag) for tag in set(body.tags.root)], owner=current_user)
    db_session.add(new_post)
    db_session.commit()
    return Post(id=str(new_post.id), content=new_post.content,
                author=new_post.owner.login, createdAt=rfc3339.rfc3339(new_post.createdAt),
                tags=[tag.tag for tag in new_post.tags], likesCount=new_post.liked_users.count(),
                dislikesCount=new_post.disliked_users.count())


@router.get(
    '/posts/{post_id}',
    response_model=Union[Post, ErrorResponse],
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def get_post_by_id(
        response: Response, post_id: Annotated[uuid.UUID, PostId], current_user=Depends(get_current_user),
        db_session=Depends(get_session)
) -> Union[Post, ErrorResponse]:
    """
    Получить ленту со своими постами
    """
    try:
        post = db_session.query(DBPost).where(DBPost.id == post_id.root).first()  # noqa
    except:
        response.status_code = 404
        return ErrorResponse(reason="post not found")
    if not post:
        response.status_code = 404
        return ErrorResponse(reason="post not found")
    if not post.owner.isPublic and post.owner != current_user and current_user not in post.owner.friends:
        response.status_code = 404
        return ErrorResponse(reason="post not found")
    return Post(id=str(post.id), content=post.content,
                author=post.owner.login, createdAt=rfc3339.rfc3339(post.createdAt),
                tags=[tag.tag for tag in post.tags], likesCount=post.liked_users.count(),
                dislikesCount=post.disliked_users.count())


@router.post(
    '/posts/{post_id}/dislike',
    response_model=Union[Post, ErrorResponse],
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def dislike_post(
        response: Response, post_id: Annotated[uuid.UUID, PostId], current_user=Depends(get_current_user),
        db_session=Depends(get_session)
) -> Union[Post, ErrorResponse]:
    """
    Дизлайк поста
    """
    try:
        post = db_session.query(DBPost).where(DBPost.id == post_id.root).first()  # noqa
    except:
        response.status_code = 404
        return ErrorResponse(reason="post not found")
    if not post:
        response.status_code = 404
        return ErrorResponse(reason="post not found")
    if not post.owner.isPublic and post.owner != current_user and current_user not in post.owner.friends:
        response.status_code = 404
        return ErrorResponse(reason="post not found")
    insert_stmt = insert(post_rates).values(
        user_id=current_user.id,
        post_id=str(post_id.root), # noqa
        rate_type=-1)
    insert_stmt = insert_stmt.on_conflict_do_update(
        constraint='_post_rates_uc',
        set_={"rate_type": -1})
    db_session.execute(insert_stmt)
    db_session.commit()
    db_session.refresh(post)
    return Post(id=str(post.id), content=post.content,
                author=post.owner.login, createdAt=rfc3339.rfc3339(post.createdAt),
                tags=[tag.tag for tag in post.tags], likesCount=post.liked_users.count(),
                dislikesCount=post.disliked_users.count())


@router.post(
    '/posts/{post_id}/like',
    response_model=Union[Post, ErrorResponse],
    responses={'401': {'model': ErrorResponse}, '404': {'model': ErrorResponse}},
)
def like_post(
        response: Response, post_id: Annotated[uuid.UUID, PostId], current_user=Depends(get_current_user),
        db_session=Depends(get_session)
) -> Union[Post, ErrorResponse]:
    """
    Лайк поста
    """
    try:
        post = db_session.query(DBPost).where(DBPost.id == post_id.root).first()  # noqa
    except:
        response.status_code = 404
        return ErrorResponse(reason="post not found")
    if not post:
        response.status_code = 404
        return ErrorResponse(reason="post not found")
    if not post.owner.isPublic and post.owner != current_user and current_user not in post.owner.friends:
        response.status_code = 404
        return ErrorResponse(reason="post not found")
    insert_stmt = insert(post_rates).values(
        user_id=current_user.id,
        post_id=str(post_id.root), # noqa
        rate_type=1)
    insert_stmt = insert_stmt.on_conflict_do_update(
        constraint='_post_rates_uc',
        set_={"rate_type": 1})
    db_session.execute(insert_stmt)
    db_session.commit()
    db_session.refresh(post)
    return Post(id=str(post.id), content=post.content,
                author=post.owner.login, createdAt=rfc3339.rfc3339(post.createdAt),
                tags=[tag.tag for tag in post.tags], likesCount=post.liked_users.count(),
                dislikesCount=post.disliked_users.count())


@router.get(
    '/profiles/{login}',
    response_model=Union[UserProfile, ErrorResponse],
    response_model_exclude_none=True,
    responses={'401': {'model': ErrorResponse}, '403': {'model': ErrorResponse}},
)
def get_profile(response: Response, login: Annotated[str, UserLogin], current_user=Depends(get_current_user),
                db_session: Session = Depends(get_session)) -> Union[UserProfile, ErrorResponse]:
    """
    Получение профиля пользователя по логину
    """
    user_account = db_session.query(DBUser).filter(DBUser.login == login.root).first()
    if user_account is None or (not user_account.isPublic and (
            login.root != current_user.login and current_user not in user_account.friends)):
        response.status_code = 403
        return ErrorResponse(reason="access denied")
    return user_account


app.include_router(router)
