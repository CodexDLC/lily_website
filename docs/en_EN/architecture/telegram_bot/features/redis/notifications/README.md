# 📂 Notifications (Redis Feature)

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

This feature is dedicated to processing and delivering various types of asynchronous notifications to Telegram users. It acts as a consumer for notification messages published to Redis Streams, ensuring reliable and scalable delivery of information such as booking updates, system alerts, or personalized messages. The module is designed to be highly decoupled from the notification source, allowing for flexible integration with different backend services.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📜 Feature Setting](./feature_setting.md)** | Configuration for the Redis Notifications feature |
| **[📂 Logic](./logic/README.md)** | Business logic for notification processing and delivery |
| **[📂 Handlers](./handlers/README.md)** | Handlers for processing notification messages from Redis |
| **[📂 UI](./ui/README.md)** | User interface components related to notification display |
| **[📂 Contracts](./contracts/README.md)** | Data contracts (DTOs) for notification messages |
| **[📂 Resources](./resources/README.md)** | Static resources (e.g., texts, keyboards) for notifications |
