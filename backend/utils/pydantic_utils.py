from pydantic import BaseModel
from bson import ObjectId


def pass_fields(to_model: BaseModel, from_object: BaseModel, **kwargs) -> BaseModel:
    return to_model(**from_object.model_dump(include=set(to_model.model_fields.keys())), **kwargs)


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, field):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId format")
        return str(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, handler):
        return {'type': 'string'}