from pydantic import BaseModel


class ChatBase(BaseModel):
    prompt: str
    response: str | None = None


class ChatCreate(ChatBase):
    pass


class Chats(ChatBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    items: list[Chats] = []

    class Config:
        from_attributes = True
