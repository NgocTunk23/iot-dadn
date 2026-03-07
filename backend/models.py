from pydantic import BaseModel, Field
from datetime import datetime

class SensorData(BaseModel):
    # Sử dụng alias để map timestamp vào _id của MongoDB
    id: datetime = Field(alias="_id") 
    timestamp: datetime
    temp: float
    humi: float
    light: int

    class Config:
        populate_by_name = True # Cho phép dùng cả '_id' và 'id'