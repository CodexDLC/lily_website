# 📜 API Client

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../README.md)

This module defines the `BaseApiClient` class, an abstract base class for making asynchronous HTTP requests to external APIs. It provides common functionality for handling API requests, including setting headers, managing timeouts, and error handling.

## `BaseApiClient` Class

The `BaseApiClient` serves as a foundation for specific API clients within the application. It encapsulates the logic for sending HTTP requests and processing responses.

### Initialization (`__init__`)

```python
def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 10.0):
```
Initializes the API client.

*   `base_url` (str): The base URL for the API.
*   `api_key` (str | None): Optional API key for authentication, added as `X-API-Key` header.
*   `timeout` (float): Request timeout in seconds.

### Request Method (`_request`)

```python
async def _request(
    self,
    method: str,
    endpoint: str,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | Any:
```
A protected asynchronous method for sending HTTP requests. This method handles the actual communication with the API, including error handling and JSON parsing.

*   `method` (str): The HTTP method (e.g., "GET", "POST", "PUT", "DELETE").
*   `endpoint` (str): The API endpoint relative to the `base_url`.
*   `json` (dict[str, Any] | None): Optional JSON payload for the request body.
*   `params` (dict[str, Any] | None): Optional query parameters.

**Error Handling:**
The method includes comprehensive error handling for `httpx.HTTPStatusError` (HTTP errors), `httpx.RequestError` (connection errors), and other general exceptions, raising `ApiClientError` in case of issues.

## `ApiClientError` Exception

```python
class ApiClientError(Exception):
    """Базовая ошибка API клиента"""
```
Custom exception class for API client-related errors.
