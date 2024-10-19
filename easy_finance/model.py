from typing import Annotated

import reflex as rx
from sqlmodel import Field


class User(rx.Model, table=True):
    id: Annotated[int, Field(primary_key=True)]
    username: str
    email: str
    password: str


rx.components