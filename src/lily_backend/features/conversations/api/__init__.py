from ninja import Router

from .campaigns import router as campaigns_router
from .import_email import router as import_email_router

router = Router()
router.add_router("/campaigns", campaigns_router)
router.add_router("", import_email_router)

__all__ = ["router"]
