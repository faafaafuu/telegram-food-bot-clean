from .catalog import router as catalog_router
from .cart import router as cart_router
from .order import router as order_router
from .admin import router as admin_router

# Expose routers for main to include
router = None

# Also export convenient names
catalog = catalog_router
cart = cart_router
order = order_router
admin = admin_router
