from typing import Any

from pydantic import BaseModel, ValidationError, validator
from argscheck import Typed


class UserModel(BaseModel):
    name: Any

    check_name = Typed(str).validator('name')


# model = UserModel(name=1234)


from uuid import UUID
from typing import Union
from pydantic import BaseModel

class User(BaseModel):
    id: Union[list, str]
    name: str

print(User(id=1, name='asd').id)