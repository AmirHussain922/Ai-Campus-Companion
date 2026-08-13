# Error Response Standardization Guide

This guide explains how to use the standardized error response system throughout your application.

## Overview

All API endpoints now use a consistent error response format:

```json
{
  "success": false,
  "error_code": "AUTH_001",
  "message": "User not found",
  "details": {},
  "request_id": "abc123"
}
```

Success responses use:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {}
}
```

## How to Use

### 1. Basic Error Response

```python
from app.core.error_responses import create_error_response

# Instead of:
# raise HTTPException(status_code=400, detail="Invalid email format")

# Use:
from fastapi import HTTPException

# Option 1: Return error response directly
return JSONResponse(
    status_code=400,
    content=create_error_response(
        message="Invalid email format",
        error_code="AUTH_002",
        details={"field": "email", "reason": "Invalid email structure"}
    )
)

# Option 2: Raise AppException (recommended)
from app.core.error_responses import AppException

raise AppException(
    message="Invalid email format",
    error_code="AUTH_002",
    status_code=status.HTTP_400_BAD_REQUEST,
    details={"field": "email", "reason": "Invalid email structure"}
)
```

### 2. Auth Response (for Login/Registration)

```python
from app.core.error_responses import create_auth_response

# On successful registration
return JSONResponse(
    status_code=201,
    content=create_auth_response(
        success=True,
        message="User registered successfully",
        user=user_data,
        access_token=access_token,
        refresh_token=refresh_token
    )
)

# On registration failure
return JSONResponse(
    status_code=400,
    content=create_auth_response(
        success=False,
        message="Email already exists",
        user=user_data  # May include existing user data
    )
)
```

### 3. Standard Success Response

```python
from app.core.error_responses import create_success_response

return JSONResponse(
    status_code=200,
    content=create_success_response(
        message="Data retrieved successfully",
        data={"items": [...]},
        success=True
    )
)
```

### 4. Data Response with Pagination

```python
from app.core.error_responses import create_success_response

return JSONResponse(
    status_code=200,
    content=create_success_response(
        message="Messages retrieved successfully",
        data={
            "items": messages,
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total_items": 100,
                "total_pages": 5
            }
        }
    )
)
```

## Error Code Standard

Error codes follow the format: `MODULE_CODE_SEQUENCE`

Examples:
- `AUTH_001` - Authentication errors
- `AUTH_002` - Authorization errors
- `AUTH_008` - Rate limit errors
- `MEM_001` - Memory service errors
- `CHAT_001` - Chat errors
- `GENERIC_ERROR` - General errors

### Common Error Codes

| Error Code | Status | Description |
|-----------|--------|-------------|
| `AUTH_001` | 401 | Invalid credentials |
| `AUTH_002` | 401 | Invalid token |
| `AUTH_003` | 403 | Unauthorized access |
| `AUTH_004` | 401 | Token expired |
| `AUTH_008` | 429 | Rate limit exceeded |
| `AUTH_009` | 500 | Email service error |
| `VALIDATION_001` | 400 | Invalid input format |
| `VALIDATION_002` | 422 | Missing required fields |
| `VALIDATION_003` | 400 | Value out of range |

## Examples by Endpoint Type

### Registration Endpoint

```python
# Success
@router.post("/register")
async def register(request: RegistrationRequest):
    # Validation
    if not email_regex.match(request.email):
        raise AppException(
            message="Invalid email format",
            error_code="VALIDATION_001",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": "email", "allowed_format": "user@domain.com"}
        )

    # Create user
    user = await auth_service.register(request)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=create_auth_response(
            message="User registered successfully",
            user=user.to_dict(),
            access_token=token,
            refresh_token=refresh_token
        )
    )

# Duplicate email
except ValueError as e:
    raise AppException(
        message="Email already exists",
        error_code="AUTH_005",
        status_code=status.HTTP_400_BAD_REQUEST
    )
```

### Login Endpoint

```python
@router.post("/login")
async def login(request: LoginRequest):
    user = await auth_service.authenticate(request.email, request.password)

    if not user:
        raise AppException(
            message="Invalid email or password",
            error_code="AUTH_001",
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    tokens = await token_service.create_tokens(user)

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=create_auth_response(
            message="Login successful",
            user=user.to_dict(),
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer"
        )
    )
```

### Chat Endpoint

```python
@router.post("/chat/send")
async def send_message(request: ChatRequest, current_user = Depends(get_current_user)):
    try:
        message = await chat_service.send_message(
            user_id=current_user["id"],
            message=request.message
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=create_success_response(
                message="Message sent successfully",
                data=message.to_dict()
            )
        )
    except InvalidMessageError as e:
        raise AppException(
            message="Invalid message format",
            error_code="CHAT_001",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"field": "message", "reason": str(e)}
        )
```

## Migration Guide

### From HTTPException to AppException

**Before:**
```python
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid email format"
)
```

**After:**
```python
raise AppException(
    message="Invalid email format",
    error_code="VALIDATION_001",
    status_code=status.HTTP_400_BAD_REQUEST
)
```

### From HTTPException to Error Response

**Before:**
```python
return JSONResponse(
    status_code=400,
    content={"detail": "Invalid email format"}
)
```

**After:**
```python
from app.core.error_responses import create_error_response

return JSONResponse(
    status_code=400,
    content=create_error_response(
        message="Invalid email format",
        error_code="VALIDATION_001"
    )
)
```

## Benefits

1. **Consistency**: All endpoints have the same error format
2. **Debugging**: Error codes help developers quickly identify issues
3. **Client Integration**: Clients can easily parse and handle errors
4. **Logging**: Centralized error handling with request IDs
5. **Documentation**: Error codes serve as API documentation

## Testing

All error responses can be tested using the test suite:

```python
async def test_error_response_format(client: AsyncClient):
    response = await client.post("/api/auth/login", json={})
    data = response.json()

    # All error responses have these fields
    assert "success" in data
    assert "error_code" in data
    assert "message" in data
    assert "request_id" in data
    assert data["success"] is False
```
