"""
Authentication for Admin Panel
"""
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from loguru import logger


class AdminAuth(AuthenticationBackend):
    """Simple username/password authentication for admin panel"""
    
    # Учетные данные для доступа в админ-панель
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "D7eva123qwerty"
    
    async def login(self, request: Request) -> bool:
        """
        Handle login request
        """
        form = await request.form()
        username = form.get("username", "")
        password = form.get("password", "")
        
        logger.info(f"Admin login attempt: username={username}")
        
        if username == self.ADMIN_USERNAME and password == self.ADMIN_PASSWORD:
            # Сохраняем в сессии что пользователь аутентифицирован
            request.session.update({"admin_authenticated": True})
            logger.info(f"Admin login successful, session: {request.session}")
            return True
        
        logger.warning(f"Admin login failed for username={username}")
        return False
    
    async def logout(self, request: Request) -> bool:
        """
        Handle logout request
        """
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        """
        Check if user is authenticated
        """
        is_auth = request.session.get("admin_authenticated", False)
        logger.debug(f"Admin authenticate check: {is_auth}, session: {dict(request.session)}")
        return is_auth


def create_admin_auth() -> AdminAuth:
    """
    Create admin authentication backend
    """
    # Secret key берется из SessionMiddleware, не передаем его сюда
    return AdminAuth(secret_key="your-super-secret-key-change-in-production-please")
