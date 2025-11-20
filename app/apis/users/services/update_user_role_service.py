from apis.auth.utils import RolesBasedAuthChecker, get_current_user, update_user
from apis.users.schemas import UserRoleUpdate
from db import models
from db.session import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.put("/users/update_role", response_model=UserRoleUpdate)
async def update_user_role(
    user: UserRoleUpdate,
    current_user: Annotated[models.User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    """
    CORRECCIÓN DE LA VULNERABILIDAD: PRIVILEGE ESCALATION (Escalada de Privilegios)

    Antes:
        - Cualquier usuario autenticado podía cambiar el rol de otro usuario.
        - Esto permitía que un CUSTOMER se convirtiera en EMPLOYEE (escalada de privilegios).
        - Vulnerabilidad clasificada como Broken Access Control (OWASP A01).

    Ahora:
        - Solo usuarios con rol EMPLOYEE o CHEF pueden cambiar roles.
        - Solo el rol CHEF puede asignar el rol CHEF.
        - Se evita que los usuarios se auto-asignen privilegios elevados.
    """

    #  Verificar si el usuario actual tiene permisos para cambiar roles
    if current_user.role not in (models.UserRole.EMPLOYEE, models.UserRole.CHEF):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para cambiar roles. Solo empleados y chef pueden realizar esta acción.",
        )

    # Evitar que un empleado asigna el rol CHEF
    if user.role == models.UserRole.CHEF.value and current_user.role != models.UserRole.CHEF:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo un usuario con rol CHEF puede asignar el rol CHEF.",
        )

    # Verificar si el usuario objetivo existe
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario especificado no existe.",
        )

    # Si el usuario objetivo ya tiene ese rol, evitar cambios innecesarios
    if db_user.role == user.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene asignado este rol.",
        )

    # Actualizar el rol del usuario en la base de datos
    updated_user = update_user(db, user.username, user)

    return updated_user
