"""
Create test data for development
"""
import sys
sys.path.insert(0, '/app')

from app.database import SessionLocal
from app.models.company import Company
from app.models.user import User
from app.models.sip_trunk import SIPTrunk
from app.models.phone_number import PhoneNumber
from app.core.security import get_password_hash

def create_test_data():
    db = SessionLocal()
    
    try:
        # Create test company
        company = Company(
            name="Тестовая компания",
            domain="test.local",
            ai_enabled=True
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        print(f"✅ Created company: {company.name} (ID: {company.id})")
        
        # Create admin user
        admin = User(
            company_id=company.id,
            username="admin",
            password_hash=get_password_hash("admin123"),
            full_name="Администратор",
            email="admin@test.local",
            role="admin",
            sip_username="admin-sip",
            sip_password="admin123",
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"✅ Created admin: {admin.username} (password: admin123)")
        
        # Create operator user
        operator = User(
            company_id=company.id,
            username="operator",
            password_hash=get_password_hash("operator123"),
            full_name="Оператор Тестовый",
            email="operator@test.local",
            role="operator",
            sip_username="operator",
            sip_password="operator123",
            is_active=True
        )
        db.add(operator)
        db.commit()
        db.refresh(operator)
        print(f"✅ Created operator: {operator.username} (password: operator123)")
        
        # Create SIP trunk (Mango Office)
        trunk = SIPTrunk(
            company_id=company.id,
            name="Mango Office",
            provider="mango",
            server_uri="sip:aiagent.mangosip.ru",
            client_uri="sip:operator1@aiagent.mangosip.ru",
            username="operator1@aiagent.mangosip.ru",
            password="D7eva123qwerty!",
            realm="aiagent.mangosip.ru",
            enabled=True
        )
        db.add(trunk)
        db.commit()
        db.refresh(trunk)
        print(f"✅ Created SIP trunk: {trunk.name} (ID: {trunk.id})")
        
        # Create phone number
        phone = PhoneNumber(
            company_id=company.id,
            trunk_id=trunk.id,
            number="+79918987423",
            display_name="Основной номер",
            is_available=True
        )
        db.add(phone)
        db.commit()
        db.refresh(phone)
        print(f"✅ Created phone number: {phone.number} (ID: {phone.id})")
        
        print("\n" + "="*50)
        print("🎉 Test data created successfully!")
        print("="*50)
        print(f"\n📊 Summary:")
        print(f"  Company: {company.name}")
        print(f"  Admin: admin / admin123")
        print(f"  Operator: operator / operator123")
        print(f"  SIP Trunk: {trunk.name}")
        print(f"  Phone: {phone.number}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()
