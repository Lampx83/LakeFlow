from fastapi import APIRouter, HTTPException, status, Depends

from lakeflow.api.schemas.auth import LoginRequest, TokenResponse
from lakeflow.i18n import i18n_detail
from lakeflow.core.auth import verify_token
from lakeflow.services.auth_service import authenticate

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    token = authenticate(data.username, data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=i18n_detail("auth.invalid_credentials"),
        )

    return {"access_token": token}


@router.get("/me")
def me(payload: dict = Depends(verify_token)):
    """Return current user info from token (used to filter history per account)."""
    return {"username": payload["sub"]}
