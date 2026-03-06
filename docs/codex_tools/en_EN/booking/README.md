# 📅 Booking Module

[⬅️ Back to Docs Root](../../README.md)

This module encapsulates the business logic for calculating available slots and optimizing multi-service (chained) booking appointments. It operates strictly on plain Python data structures, avoiding any tight coupling with an ORM.

## 🗺️ Module Map

| Component | Description |
|:---|:---|
| **[📄 Data Transfer Objects (DTO)](./dto.md)** | `frozen=True` Pydantic schemas defining inputs and outputs. |
| **[📄 Core Engine](./engine.md)** | `ChainFinder` and `SlotCalculator` algorithms. |
| **[📄 Interfaces & Adapters](./interfaces_and_adapters.md)** | How this module connects with external databases like Django. |

## Quick Overview

The booking engine is designed to answer a primary question: *"When is a professional available to perform service X, and if there are multiple services in a chain, how do they fit together?"*

It supports:
1. Single service searches.
2. Sequential chains executed by one professional.
3. Chains where services can be performed in parallel or overlapping.
4. Breaks, dynamic minimum start times (e.g. "no sooner than 2 hours from now"), and variable padding (gaps) between sessions.
