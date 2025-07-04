from fastapi import APIRouter

from todo_api.metrics import router as metrics_router
from todo_api.todos.router import router as todos_router
from todo_api.users.router import router as users_router

router_v1 = APIRouter(prefix="/v1")

router_v1.include_router(metrics_router)
router_v1.include_router(todos_router)
router_v1.include_router(users_router)
