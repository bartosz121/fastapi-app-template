from fastapi import APIRouter

from todo_api.api.routers.metrics import router as metrics_router
from todo_api.api.routers.todos import router as todos_router
from todo_api.api.routers.users import router as users_router

router_v1 = APIRouter(prefix="/v1")

router_v1.include_router(metrics_router)
router_v1.include_router(todos_router)
router_v1.include_router(users_router)
