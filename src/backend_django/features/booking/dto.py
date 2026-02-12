from dataclasses import asdict, dataclass
from datetime import date, datetime


@dataclass
class BookingState:
    """
    DTO for storing booking wizard state.
    """

    step: int = 1
    category_slug: str | None = None
    service_id: int | None = None
    master_id: str | None = None

    selected_date: date | None = None
    selected_time: str | None = None

    def to_dict(self) -> dict:
        """Serialization for session (date -> str)."""
        data = asdict(self)
        if self.selected_date:
            data["selected_date"] = self.selected_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "BookingState":
        """Deserialization from session (str -> date)."""
        # Filter keys to match dataclass fields
        valid_keys = {k for k in cls.__annotations__}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}

        # Handle date conversion
        if (
            "selected_date" in filtered_data
            and filtered_data["selected_date"]
            and isinstance(filtered_data["selected_date"], str)
        ):
            try:
                filtered_data["selected_date"] = datetime.strptime(filtered_data["selected_date"], "%Y-%m-%d").date()
            except ValueError:
                filtered_data["selected_date"] = None

        # Handle step conversion (ensure int)
        if "step" in filtered_data:
            try:
                filtered_data["step"] = int(filtered_data["step"])
            except (ValueError, TypeError):
                filtered_data["step"] = 1

        # Handle service_id conversion (ensure int if present)
        if "service_id" in filtered_data and filtered_data["service_id"]:
            try:
                filtered_data["service_id"] = int(filtered_data["service_id"])
            except (ValueError, TypeError):
                filtered_data["service_id"] = None

        return cls(**filtered_data)
