# ⚙️ Booking Engine Core

[⬅️ Back](./README.md) | [🏠 Docs Root](../../README.md)

The core logic resides in `codex_tools.booking`. It leverages sliding-window paradigms to dissect free times in schedules.

## `SlotCalculator`

Extracted pure functions for temporal calculations.
- `merge_free_windows`: Subtracts `busy_intervals` and `break_intervals` from the professional's `work_hours`, providing a list of continuous `free_windows`.
- `find_slots_in_window`: Given a `window_start` and `window_end`, a `duration_minutes`, and a `step_minutes` grid (default 30 min), calculates all valid `grid_origin` alignment starts.

## `ChainFinder`

The orchestrator. It executes a backtracking algorithm to map `[Service_A, Service_B]` into `[(Master_1, 10:00), (Master_1, 11:30)]`.

### Algorithm Execution Flow:
1. Validates `BookingEngineRequest`.
2. Receives `dict[master_id: MasterAvailability]` (calculated by an adapter).
3. If processing a single day:
   - For each service in the chain, attempts to bind it to a master's free window.
   - Pushes the tentative slot to a temporary stack (`_SlotCandidate`).
   - If binding fails, pops and tries the next available slot or master.
   - Saves completed stacks as `BookingChainSolution`.
4. Returns an `EngineResult` mapped, sorted, and optionally grouped by start times.

**Performance Characteristics:**
The engine bypasses heavy Pydantic validations inside the `backtrack()` method by using bare `__slots__` lightweight candidate classes. It dynamically scales up to `10,000` combinations in sub-millisecond ranges.
