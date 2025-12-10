from pydantic import BaseModel

# User
class QueryRequest(BaseModel):
    query: str

