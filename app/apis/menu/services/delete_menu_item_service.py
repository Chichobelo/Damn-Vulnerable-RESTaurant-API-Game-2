from apis.auth.utils import RolesBasedAuthChecker, get_current_user
from apis.menu import utils
from db.models import User, UserRole
from db.session import get_db
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing_extensions import Annotated

router = APIRouter()


@router.delete("/menu/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    item_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Session = Depends(get_db),
):
    # CORRECCIÓN DE LA VULNERABILIDAD:
    # Antes, cualquier usuario autenticado podía eliminar un ítem.
    # Eso representaba un caso de "Broken Access Control".
    # Ahora solo los usuarios con rol EMPLOYEE o CHEF pueden eliminar ítems.
    # Esto implementa un control de autorización basado en roles (RBAC).

    if current_user.role not in (UserRole.EMPLOYEE, UserRole.CHEF):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: insufficient permissions"
        )

    # Si el rol es válido, se procede con la eliminación.
    utils.delete_menu_item(db, item_id)
