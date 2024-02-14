from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ChatApp.models import User, Chat  # Assuming models.py is in a sibling directory
from ChatApp.schemas import (
    UserCreate,
    ChatCreate,
)  # Assuming schemas.py is in a sibling directory
from ChatApp.database import get_db
from ChatApp.controller import create_access_token, authenticate_user
from ChatApp.models import Chat, User
from ChatApp.utils import sanitize_html
from passlib.context import CryptContext
from datetime import datetime
from sqlalchemy.orm import Session
from bcrypt import gensalt, hashpw
from typing import List, Optional

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def get_user(db: Session, user_id: int) -> User | None:
    """
    Retrieves a user by their ID from the database.

    Args:
        db (Session): Database session object.
        user_id (int): ID of the user to retrieve.

    Returns:
        models.User: The user object if found, None otherwise.
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Retrieves a user by their email address from the database.

    Args:
        db (Session): Database session object.
        email (str): Email address of the user to retrieve.

    Returns:
        models.User: The user object if found, None otherwise.
    """

    try:
        return db.query(User).filter(User.email == email).first()
    except Exception as e:
        # Log the exception details for debugging
        print(f"Error retrieving user by email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user",
        )


def get_users(
    db: Session, active_only: bool = True, skip: int = 0, limit: int = 100
) -> List[User]:
    """
    Retrieves a list of users from the database, optionally filtered by active status.

    Args:
        db (Session): Database session object.
        active_only (bool, optional): Whether to filter only active users. Defaults to True.
        skip (int, optional): Number of users to skip. Defaults to 0.
        limit (int, optional): Maximum number of users to return. Defaults to 100.

    Returns:
        List[models.User]: List of retrieved users.
    """

    try:
        query = db.query(User)
        if active_only:
            query = query.filter(
                User.is_active == True
            )  # Assuming you have an "is_active" field
        return query.offset(skip).limit(limit).all()
    except Exception as e:
        print(f"Error retrieving users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users",
        )


def create_user(db: Session, user: UserCreate) -> User:
    """
    Creates a new user in the database.

    Args:
        db (Session): Database session object.
        user (schemas.UserCreate): User data to be created.

    Returns:
        models.User: The created user object.

    Raises:
        HTTPException: If user creation fails due to validation errors or other reasons.
    """

    # Validate user data
    if not user.email or not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required fields"
        )

    # Hash the password
    hashed_password = hashpw(user.password.encode("utf-8"), gensalt())

    # Create user object
    db_user = User(email=user.email, hashed_password=hashed_password)

    # Add and commit to database
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {e}",
        )

    return db_user


# Define your dependency for user authentication
async def get_current_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> User:
    """
    Retrieves the current user based on authentication information.

    Args:
        form_data (OAuth2PasswordRequestForm, optional): Authentication data. Defaults to Depends().

    Returns:
        models.User: The authenticated user object.

    Raises:
        HTTPException: If authentication fails or user information cannot be retrieved.
    """

    # Authenticate user (replace with your actual implementation)
    user = authenticate_user(
        form_data.username, form_data.password
    )  # Assuming you have an "authenticate_user" function
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Retrieve user information from the database (adapt to your model structure)
    db_user = get_user_by_email(get_db, user.email)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information",
        )

    return db_user


async def get_chats(
    db: Session,
    user_id: int,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    content: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Chat]:
    """Retrieves chats based on user, date, content, and pagination.

    Args:
        db (Session): Database session object.
        user_id (int): ID of the user whose chats to retrieve.
        start_date (Optional[datetime.date], optional): Start date for filtering.
        end_date (Optional[datetime.date], optional): End date for filtering.
        content (Optional[str], optional): Content keyword for filtering.
        skip (int, optional): Number of chats to skip. Defaults to 0.
        limit (int, optional): Maximum number of chats to return. Defaults to 100.

    Returns:
        List[models.Chat]: List of retrieved chats.
    """

    query = db.query(Chat).filter_by(owner_id=user_id)

    # Filter by date range if provided
    if start_date:
        query = query.filter(Chat.created_at >= start_date)
    if end_date:
        query = query.filter(Chat.created_at <= end_date)

    # Filter by content (case-insensitive) if provided
    if content:
        query = query.filter(Chat.content.ilike(f"%{content}%"))

    # Apply pagination
    return query.offset(skip).limit(limit).all()


async def create_user_chat(
    db: Session,
    user_id: int,
    item: ChatCreate,
) -> Chat:
    """Creates a new chat for a user with content validation and security.

    Args:
        db (Session): Database session object.
        user_id (int): ID of the user creating the chat.
        item (schemas.ChatCreate): Chat creation data.

    Returns:
        models.Chat: The created chat object.

    Raises:
        HTTPException: For validation errors or other issues.
    """

    # Validate content length and sanitize (if needed)
    if len(item.prompt) > 255:
        raise HTTPException(status_code=400, detail="Prompt is too long")
    item.prompt = sanitize_html(item.prompt)  # Implement proper sanitization logic

    # Create chat object and associate with user
    chat = Chat(**item.dict(), owner_id=user_id)

    # Add to database and commit
    db.add(chat)
    db.commit()
    db.refresh(chat)

    return chat
