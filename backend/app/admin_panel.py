"""
Admin Panel using SQLAdmin
"""
from sqladmin import Admin, ModelView
from sqlalchemy import select

from .models.company import Company
from .models.sip_trunk import SIPTrunk
from .models.phone_number import PhoneNumber
from .models.user import User
from .models.call_session import CallSession


class CompanyAdmin(ModelView, model=Company):
    """Admin for Company model"""
    name = "Компания"
    name_plural = "Компании"
    icon = "fa-solid fa-building"
    
    # Columns to display in list view
    column_list = [Company.id, Company.name, Company.domain, Company.ai_enabled, Company.is_active, Company.created_at]
    column_searchable_list = [Company.name, Company.domain]
    column_sortable_list = [Company.id, Company.name, Company.created_at]
    column_default_sort = [(Company.created_at, True)]
    
    # Columns in detail view
    column_details_list = [
        Company.id,
        Company.name,
        Company.domain,
        Company.ai_enabled,
        Company.is_active,
        Company.settings,
        Company.created_at
    ]
    
    # Form fields
    form_columns = [
        Company.name,
        Company.domain,
        Company.ai_enabled,
        Company.is_active,
        Company.settings
    ]
    
    # Column labels
    column_labels = {
        Company.id: "ID",
        Company.name: "Название",
        Company.domain: "Домен",
        Company.ai_enabled: "AI включен",
        Company.is_active: "Активна",
        Company.settings: "Настройки",
        Company.created_at: "Создана"
    }


class SIPTrunkAdmin(ModelView, model=SIPTrunk):
    """Admin for SIP Trunk model"""
    name = "SIP Транк"
    name_plural = "SIP Транки"
    icon = "fa-solid fa-phone-volume"
    
    column_list = [
        SIPTrunk.id,
        SIPTrunk.company_id,
        SIPTrunk.name,
        SIPTrunk.provider,
        SIPTrunk.server_uri,
        SIPTrunk.enabled,
        SIPTrunk.created_at
    ]
    
    column_searchable_list = [SIPTrunk.name, SIPTrunk.provider, SIPTrunk.server_uri]
    column_sortable_list = [SIPTrunk.id, SIPTrunk.name, SIPTrunk.created_at]
    column_default_sort = [(SIPTrunk.created_at, True)]
    
    form_columns = [
        SIPTrunk.company_id,
        SIPTrunk.name,
        SIPTrunk.provider,
        SIPTrunk.server_uri,
        SIPTrunk.client_uri,
        SIPTrunk.username,
        SIPTrunk.password,
        SIPTrunk.realm,
        SIPTrunk.enabled
    ]
    
    column_labels = {
        SIPTrunk.id: "ID",
        SIPTrunk.company_id: "Компания ID",
        SIPTrunk.name: "Название",
        SIPTrunk.provider: "Провайдер",
        SIPTrunk.server_uri: "Server URI",
        SIPTrunk.client_uri: "Client URI",
        SIPTrunk.username: "Логин",
        SIPTrunk.password: "Пароль",
        SIPTrunk.realm: "Realm",
        SIPTrunk.enabled: "Включен",
        SIPTrunk.created_at: "Создан"
    }
    
    # Hide password in list view
    column_formatters = {
        SIPTrunk.password: lambda m, a: "********" if m.password else ""
    }


class PhoneNumberAdmin(ModelView, model=PhoneNumber):
    """Admin for Phone Number model"""
    name = "Телефонный номер"
    name_plural = "Телефонные номера"
    icon = "fa-solid fa-phone"
    
    column_list = [
        PhoneNumber.id,
        PhoneNumber.company_id,
        PhoneNumber.trunk_id,
        PhoneNumber.number,
        PhoneNumber.display_name,
        PhoneNumber.is_available,
        PhoneNumber.assigned_user_id,
        PhoneNumber.created_at
    ]
    
    column_searchable_list = [PhoneNumber.number, PhoneNumber.display_name]
    column_sortable_list = [PhoneNumber.id, PhoneNumber.number, PhoneNumber.created_at]
    column_default_sort = [(PhoneNumber.created_at, True)]
    
    form_columns = [
        PhoneNumber.company_id,
        PhoneNumber.trunk_id,
        PhoneNumber.number,
        PhoneNumber.display_name,
        PhoneNumber.is_available,
        PhoneNumber.assigned_user_id
    ]
    
    column_labels = {
        PhoneNumber.id: "ID",
        PhoneNumber.company_id: "Компания ID",
        PhoneNumber.trunk_id: "Транк ID",
        PhoneNumber.number: "Номер",
        PhoneNumber.display_name: "Название",
        PhoneNumber.is_available: "Доступен",
        PhoneNumber.assigned_user_id: "Назначен пользователю",
        PhoneNumber.created_at: "Создан"
    }


class UserAdmin(ModelView, model=User):
    """Admin for User model"""
    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    
    column_list = [
        User.id,
        User.company_id,
        User.username,
        User.full_name,
        User.email,
        User.role,
        User.sip_username,
        User.is_active,
        User.created_at
    ]
    
    column_searchable_list = [User.username, User.full_name, User.email, User.sip_username]
    column_sortable_list = [User.id, User.username, User.created_at]
    column_default_sort = [(User.created_at, True)]
    
    form_columns = [
        User.company_id,
        User.username,
        User.full_name,
        User.email,
        User.role,
        User.sip_username,
        User.sip_password,
        User.current_number_id,
        User.is_active
    ]
    
    column_labels = {
        User.id: "ID",
        User.company_id: "Компания ID",
        User.username: "Логин",
        User.full_name: "ФИО",
        User.email: "Email",
        User.role: "Роль",
        User.sip_username: "SIP логин",
        User.sip_password: "SIP пароль",
        User.current_number_id: "Текущий номер",
        User.is_active: "Активен",
        User.created_at: "Создан"
    }
    
    # Hide passwords in list view
    column_formatters = {
        User.password_hash: lambda m, a: "********" if m.password_hash else "",
        User.sip_password: lambda m, a: "********" if m.sip_password else ""
    }


class CallSessionAdmin(ModelView, model=CallSession):
    """Admin for Call Session model"""
    name = "Сессия звонка"
    name_plural = "Сессии звонков"
    icon = "fa-solid fa-phone-slash"
    
    column_list = [
        CallSession.id,
        CallSession.company_id,
        CallSession.user_id,
        CallSession.caller_number,
        CallSession.called_number,
        CallSession.direction,
        CallSession.status,
        CallSession.started_at,
        CallSession.ended_at
    ]
    
    column_searchable_list = [CallSession.caller_number, CallSession.called_number]
    column_sortable_list = [CallSession.id, CallSession.started_at, CallSession.ended_at]
    column_default_sort = [(CallSession.started_at, True)]
    
    # Read-only for call sessions (historical data)
    can_create = False
    can_edit = False
    can_delete = True  # Allow cleanup of old data
    
    column_labels = {
        CallSession.id: "ID",
        CallSession.company_id: "Компания ID",
        CallSession.user_id: "Пользователь ID",
        CallSession.caller_number: "Звонящий",
        CallSession.called_number: "Принимающий",
        CallSession.direction: "Направление",
        CallSession.status: "Статус",
        CallSession.started_at: "Начало",
        CallSession.answered_at: "Ответ",
        CallSession.ended_at: "Окончание",
        CallSession.duration: "Длительность (сек)",
        CallSession.recording_path: "Запись",
        CallSession.transcript: "Транскрипт",
        CallSession.ai_summary: "AI Анализ",
        CallSession.ai_enabled: "AI включен"
    }


def setup_admin(app, engine, authentication_backend=None):
    """
    Setup SQLAdmin with FastAPI app
    
    Args:
        app: FastAPI application instance
        engine: SQLAlchemy engine
        authentication_backend: Authentication backend for admin panel
    """
    admin = Admin(
        app,
        engine,
        title="AI Call Agent - Админ Панель",
        base_url="/admin",
        authentication_backend=authentication_backend
    )
    
    # Register model views
    admin.add_view(CompanyAdmin)
    admin.add_view(SIPTrunkAdmin)
    admin.add_view(PhoneNumberAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(CallSessionAdmin)
    
    return admin
