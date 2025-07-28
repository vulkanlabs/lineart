from pydantic import BaseModel


class AuthStartResponse(BaseModel):
    authorization_url: str


class AuthUserInfoResponse(BaseModel):
    email: str
    picture: str


class AuthCompleteResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str


class AuthDisconnectResponse(BaseModel):
    message: str
