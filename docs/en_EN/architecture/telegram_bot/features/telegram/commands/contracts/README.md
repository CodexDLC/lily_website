# 📂 Commands Contracts

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../../README.md)

Data access interfaces for the Commands feature.

## 📜 Contract: AuthDataProvider

```python
class AuthDataProvider(Protocol):
    async def upsert_user(self, user_dto: UserUpsertDTO) -> None: ...
    async def logout(self, user_id: int) -> None: ...
```

**API Mode:** Implemented by `AuthClient` (HTTP calls to FastAPI backend).
**Direct Mode:** Would be implemented by `AuthRepository` (SQLAlchemy queries).
