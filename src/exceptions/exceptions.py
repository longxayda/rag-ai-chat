# ----- Operational Errors -----
# - 404 Not Found
# - 422 Unprocessible Entity
# - 500 Internal Server Error
# - 401 Unauthorized

from fastapi import HTTPException


class NotFoundException(Exception):
    def __init__(self):
        self.status_code: int = 404
        self.detail: str = "Not Found"
        
class UnauthorizedException(Exception):
    def __init__(self):
        self.status_code: int = 401
        self.detail: str = "Unauthorized"
        
class UnprocessibleEntityException(Exception):
    def __init__(self):
        self.status_code: int = 422
        self.detail: str = "Unprocessible Entity"
        
# ----- Custom Exception ------

# Base exception class for ALL custom exception in this app
class ApiException(HTTPException):
    def __init__(self, status_code: int, detail: str, error_code: str):
        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"X-Error-Code": error_code},
        )

class ChatNotFoundException(ApiException):
    def __init__(self, chat_id: str):
        super().__init__(
            status_code=400,
            detail=f"Chat {chat_id} not found",
            error_code="CHAT_NOT_FOUND",
        )
        
class UserNotFoundException(ApiException):
    def __init__(self, user_id: str):
        super().__init__(
            status_code=400, 
            detail=f"User {user_id} not found", 
            error_code="USER_NOT_FOUND"),

class DocumentNotFound(ApiException):
    def __init__(self, doc_id: str):
        super().__init__(
            status_code=400, 
            detail=f"Document {doc_id} not found", 
            error_code="DOCUMENT_NOT_FOUND"),