from .auth import router as auth_router
from .users import router as users_router
from .facilities import router as facilities_router
from .tests import router as tests_router
from .audits import router as audits_router


routers = [auth_router, users_router, facilities_router, tests_router, audits_router]