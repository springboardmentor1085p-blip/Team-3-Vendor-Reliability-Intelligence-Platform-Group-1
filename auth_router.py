"""
FastAPI Router for Authentication endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidUserDataError,
    RoleNotFoundError,
    UserAlreadyExistsError,
)
from app.database import get_db
from app.dependencies import get_auth_service, get_current_user, require_roles
from app.models.users import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login",
    description="Authenticate a user using username or email and return a JWT access token.",
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Authenticate a user and return an access token.
    """
    try:
        return await service.login(db, login_data)
    except InvalidUserDataError as e:
        if e.message == "User account is inactive.":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=e.message,
            )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Public user registration endpoint.",
)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """
    Register a new user account.
    """
    try:
        return await service.register_user(db, register_data)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except RoleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except InvalidUserDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Forgot password request",
    description="Initiate password reset process.",
)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    Process password reset request.
    """
    return await service.request_password_reset(db, forgot_data)


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password execution",
    description="Confirm password reset token and update user password.",
)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """
    Execute password reset using token and new password.
    """
    try:
        return await service.reset_password(db, reset_data)
    except InvalidUserDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Current authenticated user",
    description="Return the current authenticated active user.",
)
async def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Return the user resolved from the Bearer access token.
    """
    return current_user


@router.get(
    "/admin-check",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Admin role check",
    description="Verify that the current authenticated user has the ADMIN role.",
)
async def admin_check(
    current_user: User = Depends(require_roles("ADMIN", "Administrator")),
) -> UserResponse:
    """
    Return the authenticated user after ADMIN role authorization succeeds.
    """
    return current_user
