from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.database import get_db
from app.db.models import CryptoCategory
from app.schemas.crypto_category import (
    CryptoCategoryCreate,
    CryptoCategoryUpdate,
    CryptoCategoryResponse,
    CryptoCategoryListResponse
)

router = APIRouter(prefix="/crypto-categories", tags=["crypto-categories"])


@router.post("/", response_model=CryptoCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_crypto_category(
    category: CryptoCategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    db_category = CryptoCategory(**category.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.get("/", response_model=CryptoCategoryListResponse)
async def list_crypto_categories(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(CryptoCategory).offset(skip).limit(limit)
    result = await db.execute(query)
    categories = result.scalars().all()

    count_query = select(CryptoCategory)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return CryptoCategoryListResponse(categories=categories, total=total)


@router.get("/{category_id}", response_model=CryptoCategoryResponse)
async def get_crypto_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    category = await db.get(CryptoCategory, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crypto category with id {category_id} not found"
        )

    return category


@router.put("/{category_id}", response_model=CryptoCategoryResponse)
async def update_crypto_category(
    category_id: UUID,
    category_update: CryptoCategoryUpdate,
    db: AsyncSession = Depends(get_db)
):
    category = await db.get(CryptoCategory, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crypto category with id {category_id} not found"
        )

    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crypto_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    category = await db.get(CryptoCategory, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crypto category with id {category_id} not found"
        )

    await db.delete(category)
    await db.commit()

    return None
