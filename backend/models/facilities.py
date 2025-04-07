from pydantic import BaseModel, Field
from typing import Optional

class AddFacilityRequest(BaseModel):
    short_name: str = Field(description='Short name of facility (abbreviation)')
    full_name: str = Field(description='Full name of facility')
    description: Optional[str] = Field(default= None, description='Additional info')