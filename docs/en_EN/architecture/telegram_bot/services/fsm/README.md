# 📂 FSM Services

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../README.md)

State management utilities for features.

---

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📜 BaseStateManager](./base_manager.md)** | Draft storage for feature data in FSM |
| **[📜 Common FSM Handlers](./common_handlers.md)** | Garbage collector handler (last router) |

---

## 🎯 Overview

The FSM layer provides two things:

1. **BaseStateManager** — A helper for features that need to store temporary data (drafts, form inputs) in FSM state. Each feature gets an isolated namespace.

2. **Common FSM Handlers** — A catch-all router registered last in the chain. It deletes unwanted text messages in "garbage" states (see [Garbage Collector](../../core/garbage_collector.md)).
