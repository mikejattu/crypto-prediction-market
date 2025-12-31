from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.database import get_db
from app.db.models import Platform
from app.schemas.platform import (
    PlatformCreate,
    PlatformUpdate,
    PlatformResponse,
    PlatformListResponse,
)

router = APIRouter(prefix="/platforms", tags=["platforms"])


@router.post("/", response_model=PlatformResponse, status_code=status.HTTP_201_CREATED)
async def create_platform(platform: PlatformCreate, db: AsyncSession = Depends(get_db)):
    db_platform = Platform(**platform.model_dump())
    db.add(db_platform)
    await db.commit()
    await db.refresh(db_platform)
    return db_platform


@router.get("/", response_model=PlatformListResponse)
async def list_platforms(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    query = select(Platform).offset(skip).limit(limit)
    result = await db.execute(query)
    platforms = result.scalars().all()

    count_query = select(Platform)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return PlatformListResponse(platforms=platforms, total=total)


@router.get("/{platform_id}", response_model=PlatformResponse)
async def get_platform(platform_id: UUID, db: AsyncSession = Depends(get_db)):
    platform = await db.get(Platform, platform_id)

    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform with id {platform_id} not found",
        )

    return platform


@router.put("/{platform_id}", response_model=PlatformResponse)
async def update_platform(
    platform_id: UUID,
    platform_update: PlatformUpdate,
    db: AsyncSession = Depends(get_db),
):
    platform = await db.get(Platform, platform_id)

    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform with id {platform_id} not found",
        )

    update_data = platform_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(platform, field, value)

    await db.commit()
    await db.refresh(platform)

    return platform


@router.delete("/{platform_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_platform(platform_id: UUID, db: AsyncSession = Depends(get_db)):
    platform = await db.get(Platform, platform_id)

    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform with id {platform_id} not found",
        )

    await db.delete(platform)
    await db.commit()

    return None
