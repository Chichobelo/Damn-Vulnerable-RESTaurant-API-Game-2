from fastapi import APIRouter, Response

router = APIRouter()


@router.get("/healthcheck")
def healthcheck(response: Response):
    # Se elimina el header que filtraba información sensible
    return {"ok": True}
