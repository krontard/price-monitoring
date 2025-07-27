from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.database import get_async_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserCreate, UserUpdate
from app.utils.security import hash_password

router = APIRouter()

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Создать нового пользователя
    """
    # Проверяем, не существует ли уже пользователь с таким email
    result = await db.execute(
        select(User).where(User.email == user.email)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким email уже существует"
        )
    
    # Проверяем username
    result = await db.execute(
        select(User).where(User.username == user.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, 
            detail="Пользователь с таким username уже существует"
        )
    
    # Хешируем пароль перед сохранением
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password)
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

@router.get("/", response_model=List[UserSchema])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить список пользователей
    """
    result = await db.execute(
        select(User).offset(skip).limit(limit)
    )
    users = result.scalars().all()
    return users

@router.get("/{user_id}", response_model=UserSchema)
async def read_user(
    user_id: int, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Получить пользователя по ID
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return user

@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Обновить данные пользователя
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Обновляем только переданные поля
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password":
            # Хешируем пароль при обновлении
            setattr(user, "hashed_password", hash_password(value))
        else:
            setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, 
    db: AsyncSession = Depends(get_async_db)
):
    """
    Удалить пользователя
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    await db.delete(user)
    await db.commit()
    
    return None
