from typing import List, Literal
from pydantic import BaseModel
from datetime import date

SocialsList = Literal["vk", "tg", "rutube"]

class UniversityRequest(BaseModel):
    webname: str


class AnalyzeRequest(BaseModel):
    universities: List[UniversityRequest]
    socials: List[SocialsList]
    start_date: date
    end_date: date
