from fastapi import Depends, HTTPException, status, FastAPI, HTTPException
from sqlalchemy.orm import Session
from ChatApp.crud import (
    get_user_by_email,
    create_user,
    get_users,
    get_user,
    create_user_chat,
    get_current_user,
    get_chats,
)
from ChatApp.models import Base
from ChatApp.schemas import User, UserCreate, ChatBase, Chats, ChatCreate
from ChatApp.controller import create_access_token
from ChatApp.database import create_engine, engine, get_db
from ChatApp.openAi import call_gpt
from openai import OpenAIError

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.orm import Session

# Rate limit
# from starlette_ratelimits import RateLimiter, RequestLimiter, MemoryStorage

# Create a global rate limiter
# limiter = RateLimiter(
#     storage=MemoryStorage(),
#     default_limit=10,  # Adjust as needed
#     default_block=60,  # Adjust as needed
# )

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db=db, user=user)


@app.get("/users/", response_model=list[User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/chat/", response_model=Chats)
def create_item_for_user(user_id: int, item: ChatCreate, db: Session = Depends(get_db)):
    return create_user_chat(db=db, item=item, user_id=user_id)


# Define your login endpoint
@app.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Get the current user using the dependency
    user = await get_current_user(form_data)
    # Generate and return an access token
    access_token = create_access_token(user)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/chat/", response_model=list[Chats])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = get_chats(db, skip=skip, limit=limit)
    return items


@app.post("/chat", response_model=ChatBase)
async def create_chat(prompt: str, authorization: str = Depends(oauth2_scheme)):
    # Authenticate user
    current_user = await get_current_user(authorization)

    # Validate prompt
    # (Add validation logic based on your requirements)

    # Call OpenAI API with prompt
    try:
        response = await call_gpt(prompt)  # Assuming you have a call_gpt function
    except OpenAIError as e:
        raise HTTPException(
            status_code=status.HTTP_500, detail=f"OpenAI API error: {e}"
        )

    # Store prompt and response in database
    chat = create_user_chat(
        db=get_db(),
        item=ChatCreate(prompt=prompt, response=response, user_id=current_user.id),
    )

    return ChatBase(prompt=chat.prompt, response=chat.response)
