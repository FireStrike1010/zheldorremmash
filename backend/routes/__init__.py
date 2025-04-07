from .auth import router as auth_router
from .users import router as users_router
from .tests import router as tests_router
from .facilities import router as facilities_router

routers = [auth_router, users_router, tests_router, facilities_router]