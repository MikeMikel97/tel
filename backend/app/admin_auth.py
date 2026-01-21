"""
Authentication for Admin Panel
"""
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse


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
        
        if username == self.ADMIN_USERNAME and password == self.ADMIN_PASSWORD:
            # Сохраняем в сессии что пользователь аутентифицирован
            request.session.update({"admin_authenticated": True})
            return True
        
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
        return request.session.get("admin_authenticated", False)


def create_admin_auth() -> AdminAuth:
    """
    Create admin authentication backend
    """
    return AdminAuth(secret_key="your-secret-key-for-admin-sessions-change-in-production")
