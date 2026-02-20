# 📄 Appointment Cache Manager

[⬅️ Back](./README.md) | [🏠 Docs Root](../../../../../../../README.md)

The `AppointmentCacheManager` is a critical infrastructure component that provides temporary storage for booking data in Redis.

## 🛠️ Class: AppointmentCacheManager

Located in: `src/telegram_bot/infrastructure/redis/managers/notifications/appointment_cache.py`

This manager is used to decouple the Telegram bot from the background workers by providing a shared data source for booking details.

### 🔍 Core Methods

*   **`save(appointment_id: int | str, data: dict[str, Any])`**:
    *   Serializes the booking data into JSON and stores it in Redis.
    *   **TTL**: Defaults to 86,400 seconds (24 hours), ensuring that data is automatically cleaned up after the booking process is complete.
*   **`get(appointment_id: int | str) -> dict | None`**:
    *   Retrieves and deserializes the booking data.
    *   Used by the `NotificationsOrchestrator` to reconstruct messages and by workers to fetch details for Email/SMS delivery.
*   **`delete(appointment_id: int | str)`**:
    *   Explicitly removes the data from the cache.

## 🧩 Why is this needed?

1.  **Worker Autonomy**: Workers only receive an `appointment_id` from the task queue. They use this manager to fetch the full data, reducing the size of the task payload.
2.  **UI Reconstruction**: When a delivery status update (e.g., "Email Sent") arrives, the bot uses this cache to rebuild the original notification message with the updated status icons.
3.  **Performance**: Reduces the number of direct API calls to the Django backend by keeping frequently accessed booking data in memory.

## 📝 Usage Example

```python
# Saving data
await container.redis.appointment_cache.save(123, {"client_name": "John", ...})

# Retrieving data
data = await container.redis.appointment_cache.get(123)
```
