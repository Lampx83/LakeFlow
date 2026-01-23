from fastapi import APIRouter, HTTPException, status

from neuai.backend.schemas.auth import LoginRequest, TokenResponse
from neuai.backend.services.auth_service import authenticate

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    token = authenticate(data.username, data.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    return {"access_token": token}
