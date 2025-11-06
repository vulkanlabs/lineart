import base64
import logging
import time
from typing import Annotated

from fastapi import APIRouter, Body, Form, Header, HTTPException, Response, status
from pydantic import BaseModel

# Create router for data server endpoints
router = APIRouter(prefix="/data", tags=["data"])

logger = logging.getLogger("uvicorn.error")


class SerasaResponse(BaseModel):
    score: int
    renda_presumida: float
    restricoes_qt: int
    restricoes_valor: float


class SCRResponse(BaseModel):
    score: int


# Original data server database
db = {
    "0": {
        "name": "Admin",
        "serasa": {
            "score": 0,
            "renda_presumida": 0.0,
            "restricoes_qt": 0,
            "restricoes_valor": 0.0,
        },
        "scr": {"score": 0},
    },
    "111.111.111-11": {
        "name": "Alice",
        "serasa": {
            "score": 100,
            "renda_presumida": 3500.0,
            "restricoes_qt": 1,
            "restricoes_valor": 850.0,
        },
        "scr": {"score": 200},
    },
    "222.222.222-22": {
        "name": "Bob",
        "serasa": {
            "score": 300,
            "renda_presumida": 5200.0,
            "restricoes_qt": 2,
            "restricoes_valor": 1200.0,
        },
        "scr": {"score": 400},
    },
    "333.333.333-33": {
        "name": "Charlie",
        "serasa": {
            "score": 500,
            "renda_presumida": 7800.0,
            "restricoes_qt": 0,
            "restricoes_valor": 0.0,
        },
        "scr": {"score": 600},
    },
    "444.444.444-44": {
        "name": "David",
        "serasa": {
            "score": 700,
            "renda_presumida": 9500.0,
            "restricoes_qt": 3,
            "restricoes_valor": 2300.0,
        },
        "scr": {"score": 800},
    },
    "555.555.555-55": {
        "name": "Eve",
        "serasa": {
            "score": 900,
            "renda_presumida": 12000.0,
            "restricoes_qt": 1,
            "restricoes_valor": 500.0,
        },
        "scr": {"score": 1000},
    },
}


@router.post("/scr", response_model=SCRResponse)
def scr_data(cpf: Annotated[str, Body(embed=True)]):
    """Get SCR score data"""
    entry = db.get(cpf, None)
    if entry is None:
        return Response(status=404)
    scr_data = entry["scr"]
    response = SCRResponse.model_validate(scr_data)
    return response


@router.post("/serasa", response_model=SerasaResponse)
def serasa_data(cpf: Annotated[str, Body(embed=True)]):
    """Get Serasa score data"""
    entry = db.get(cpf, None)
    if entry is None:
        return Response(status=404)
    serasa_data = entry["serasa"]
    response = SerasaResponse.model_validate(serasa_data)
    return response


# Add auth router at root level (not under /data)
auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/basic")
def basic_auth_test(authorization: Annotated[str | None, Header()] = None):
    """Test endpoint for Basic Authentication"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not authorization.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme, expected Basic",
            headers={"WWW-Authenticate": "Basic"},
        )

    try:
        # Extract and decode credentials
        encoded_credentials = authorization.split(" ")[1]
        decoded_bytes = base64.b64decode(encoded_credentials)
        decoded_str = decoded_bytes.decode("utf-8")
        username, password = decoded_str.split(":", 1)

        # Validate credentials (test_client:test_secret)
        if username == "test_client" and password == "test_secret":
            return {
                "message": "Authentication successful",
                "authenticated": True,
                "username": username,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid credentials for user: {username}",
                headers={"WWW-Authenticate": "Basic"},
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to parse authorization header: {str(e)}",
            headers={"WWW-Authenticate": "Basic"},
        )


@auth_router.post("/token")
def token_endpoint(
    grant_type: Annotated[str, Form()],
    scope: Annotated[str | None, Form()] = None,
    authorization: Annotated[str | None, Header()] = None,
    # Additional fields for different grant types
    username: Annotated[str | None, Form()] = None,
    password: Annotated[str | None, Form()] = None,
    code: Annotated[str | None, Form()] = None,
    refresh_token: Annotated[str | None, Form()] = None,
):
    """
    OAuth 2.0 token endpoint for testing Bearer authentication.

    Supports all OAuth 2.0 grant types:
    - client_credentials: Machine-to-machine authentication
    - password: Resource Owner Password Credentials
    - authorization_code: Authorization Code flow
    - implicit: Implicit flow (deprecated but supported)
    - refresh_token: Token refresh flow
    """
    logger.info(f"Token request - grant_type: {grant_type}, scope: {scope}")

    # Extract client credentials from Authorization header (Basic Auth)
    if not authorization or not authorization.startswith("Basic "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Basic"},
        )

    try:
        # Decode Basic Auth credentials
        encoded_credentials = authorization.split(" ")[1]
        decoded_bytes = base64.b64decode(encoded_credentials)
        decoded_str = decoded_bytes.decode("utf-8")
        client_id, client_secret = decoded_str.split(":", 1)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to parse authorization header: {str(e)}",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Validate client credentials (oauth_client:oauth_secret)
    if client_id != "oauth_client" or client_secret != "oauth_secret":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    # Process based on grant type
    if grant_type == "client_credentials":
        # Machine-to-machine: Just validate client credentials (already done above)
        logger.info("Processing client_credentials grant")
        pass

    elif grant_type == "password":
        # Resource Owner Password: Validate username and password
        logger.info(f"Processing password grant for user: {username}")
        if not username or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="username and password are required for password grant",
            )
        # Mock validation - accept test_user:test_pass
        if username != "test_user" or password != "test_pass":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

    elif grant_type == "authorization_code":
        # Authorization Code: Validate authorization code
        logger.info(f"Processing authorization_code grant with code: {code}")
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="code is required for authorization_code grant",
            )
        # Mock validation - accept any code starting with "AUTH_"
        if not code.startswith("AUTH_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization code",
            )

    elif grant_type == "implicit":
        # Implicit: Deprecated flow, but we support it for testing
        # In real OAuth this wouldn't go through token endpoint
        logger.info("Processing implicit grant (deprecated)")
        logger.warning(
            "Implicit grant is deprecated and should not be used in production"
        )

    elif grant_type == "refresh_token":
        # Refresh Token: Validate refresh token
        logger.info("Processing refresh_token grant")
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="refresh_token is required for refresh_token grant",
            )
        # Mock validation - decode the refresh token
        try:
            decoded = base64.b64decode(refresh_token).decode()
            if not decoded.startswith("REFRESH_"):
                raise ValueError("Invalid refresh token format")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid refresh token",
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported grant type: {grant_type}. Supported: client_credentials, password, authorization_code, implicit, refresh_token",
        )

    # Generate access token (simple mock - just base64 encoded data)
    expires_in = 3600  # 1 hour
    # Format: client_id:timestamp:scope (3 parts for validation)
    token_data = f"{client_id}:{int(time.time())}:{scope or 'read write'}"
    access_token = base64.b64encode(token_data.encode()).decode()

    # Generate refresh token for applicable grant types
    response = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": expires_in,
        "scope": scope or "read write",
    }

    # Add refresh token for grant types that support it
    if grant_type in ["password", "authorization_code", "refresh_token"]:
        refresh_token_data = f"REFRESH_{client_id}:{int(time.time())}"
        response["refresh_token"] = base64.b64encode(
            refresh_token_data.encode()
        ).decode()

    logger.info(f"Token issued successfully for grant_type: {grant_type}")
    return response


@auth_router.get("/protected")
def protected_endpoint(authorization: Annotated[str | None, Header()] = None):
    """Protected endpoint that requires Bearer token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme, expected Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Extract and validate token
        token = authorization.split(" ")[1]

        # Decode token (simple validation - check if it's valid base64)
        decoded = base64.b64decode(token).decode()
        parts = decoded.split(":")

        if len(parts) != 3:
            raise ValueError("Invalid token format")

        client_id, timestamp, scope = parts

        # Check if token is expired (1 hour)
        token_age = time.time() - int(timestamp)
        if token_age > 3600:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "message": "Access granted",
            "authenticated": True,
            "client_id": client_id,
            "scope": scope,
            "token_age_seconds": int(token_age),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
