from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from utils.pydantic_utils import PyObjectId

class AddFacilityRequest(BaseModel):
    short_name: str = Field(description='Short name of facility (abbreviation)')
    full_name: str = Field(description='Full name of facility')
    description: Optional[str] = Field(default=None, description='Additional info')

class FacilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: PyObjectId = Field(description='ID of facility in Mongo DB')
    short_name: str = Field(description='Short name of facility (abbreviation)')
    full_name: str = Field(description='Full name of facility')
    description: Optional[str] = Field(default=None, description='Additional info')