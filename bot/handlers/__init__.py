from .user_handlers import register_user_handlers
from .admin_handlers import register_admin_handlers

def register_handlers(bot):
    register_user_handlers(bot)
    register_admin_handlers(bot)
