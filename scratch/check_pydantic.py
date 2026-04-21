
import json
from pydantic import ValidationError
from workers.notification_worker.schemas import NotificationPayload

def test_pydantic():
    data = {
        "notification_id": "nt_1",
        "recipient": {"email": "group@test.com", "first_name": "Group"},
        "group_id": 1,
        "template_name": "bk_group_confirmation",
        "items": [{"master_name": "M1"}]
    }
    try:
        payload = NotificationPayload(**data)
        print("SUCCESS")
        print(payload.model_dump())
    except ValidationError as e:
        print("VALIDATION ERROR")
        print(e.json())

if __name__ == "__main__":
    test_pydantic()
