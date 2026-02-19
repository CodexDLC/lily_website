# 📂 Base Module

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

This directory defines the base module structure and common dependencies for worker modules. It centralizes the definition of shared services and their injection into worker contexts.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📜 Dependencies](./dependencies.md)** | Common dependency providers for worker modules |
| **[📜 Email Client](./email_client.md)** | Async SMTP email client (`AsyncEmailClient`) |
| **[📜 Template Renderer](./template_renderer.md)** | Jinja2 template rendering service |
| **[📜 Twilio Service](./twilio_service.md)** | SMS and WhatsApp via Twilio API |
