# 🛠️ Common Utilities

[⬅️ Back to Docs Root](../../README.md)

The `common` folder collects "Swiss Army knife" functions and classes that are not directly related to the project's business logic, but are essential for any serious service. They are generalized to ensure they do not depend on any specific framework logic.

## 🏗️ Why are they here?
Often, developers write a phone parser or logger configuration right in the `core/` or `utils/` folder inside a Django application. This makes the code "nailed" to the framework.

Placing such things in `codex_tools/common` aims to create a **"Base Layer"**.

## 🗂️ Included Utilities

### `logger.py`
An uncompromising choice in favor of `loguru`. This file solves a classic Python problem: how to force all third-party libraries using the default `logging` module to write beautiful colored logs with file rotation, without setting up massive `LOGGING` dictionaries in `settings.py`.
- Connects standard `logging` outputs to `loguru` via `InterceptHandler`.
- Configures colored stdout logs.
- Automatically handles JSON error files and zipped rotation.
- Silences noisy library logs (like `django.db.backends` which would spam SQL queries).

### `arq_client.py`
Often, it is necessary to enqueue a task from a regular synchronous Django view into an asynchronous Redis queue.
Provides `BaseArqClient`, an abstract producer for the `arq` asynchronous task queue.
- The built-in wrapper creates an event-loop on the fly and hides all the complexity of working with ARQ pools.
- Allows pushing jobs to a Redis pool from synchronous code.

### `cache.py`
Interface abstractions for basic caching scenarios. Currently mostly a signature structure ready to be plugged into standard memory or redis caching mechanisms based on specific deployment.

### `phone.py` & `text.py`
Pure functions for data validation and normalization without using ORM validators.
- **`phone.py`**: A simple robust phone normalizer (`normalize_phone`) that strips extraneous characters and transforms German local numbers (`0151...`) into international formats (`49151...`).
- **`text.py`**: Tools for name normalizations (e.g., capitalizing hyphenated names) and removing invisible spacing artifacts.
