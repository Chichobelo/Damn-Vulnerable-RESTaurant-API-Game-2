# app/apis/auth/services/update_profile_service.py
from typing import Union
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing_extensions import Annotated
from pydantic import BaseModel

from apis.auth.utils import get_current_user, get_user_by_username
from db.models import User, UserRole
from db.session import get_db

router = APIRouter()

class UserUpdate(BaseModel):
    username: str
    first_name: Union[str, None] = None
    last_name: Union[str, None] = None
    phone_number: Union[str, None] = None


@router.put("/profile", response_model=UserUpdate, status_code=status.HTTP_200_OK)
def update_profile(
    user: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    # --- Seguridad: si intenta modificar otro perfil, solo CHEF (o ADMIN si existe) puede hacerlo
    if user.username != current_user.username:
        # tolerancia si UserRole no define ADMIN
        allowed_roles = {UserRole.CHEF}
        if hasattr(UserRole, "ADMIN"):
            allowed_roles.add(UserRole.ADMIN)
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="You are not allowed to modify other users' profiles.")

    # --- Obtener el usuario objetivo
    db_user = get_user_by_username(db, user.username)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # --- Actualizar solo campos válidos (no cambiar username)
    data = user.dict()
    for field in ("first_name", "last_name", "phone_number"):
        val = data.get(field)
        if val is not None:
            setattr(db_user, field, val)

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
