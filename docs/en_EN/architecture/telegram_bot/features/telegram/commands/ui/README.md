# 📂 Commands UI

[⬅️ Back](../README.md) | [🏠 Docs Root](../../../../../../../README.md)

Pure rendering layer for the Commands feature. No side effects, no API calls.

## 🎨 Class: CommandsUI

```python
class CommandsUI:
    def render_start_screen(self, user_name: str) -> ViewResultDTO:
        # Combines texts.START_GREETING + keyboards.build_start_keyboard()
```
