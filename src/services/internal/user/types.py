from typing import TypedDict


class UserCreate(TypedDict):
    login: str
    password: str


class UserUpdate(TypedDict, total=False):
    login: str
    password: str
