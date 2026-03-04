from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.user import User, UserRole

router = APIRouter()

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email,
            "full_name": current_user.full_name, "role": current_user.role.value,
            "department": current_user.department}

@router.get("/")
async def list_users(db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN))):
    result = await db.execute(select(User).where(User.is_active == True))
    users = result.scalars().all()
    return [{"id": u.id, "email": u.email, "full_name": u.full_name,
             "role": u.role.value, "department": u.department} for u in users]
