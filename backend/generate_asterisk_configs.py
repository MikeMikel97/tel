#!/usr/bin/env python3
"""
Скрипт для генерации конфигурационных файлов Asterisk из БД
"""
from app.database import SessionLocal
from app.services.asterisk_config_generator import AsteriskConfigGenerator
from loguru import logger

def main():
    """Генерирует конфигурационные файлы Asterisk"""
    db = SessionLocal()
    
    try:
        logger.info("🔧 Запуск генерации конфигурационных файлов Asterisk...")
        
        generator = AsteriskConfigGenerator()
        result = generator.generate_all_configs(db)
        
        logger.success("✅ Конфигурационные файлы успешно сгенерированы!")
        logger.info(f"   PJSIP: {result.get('pjsip_file')}")
        logger.info(f"   Extensions: {result.get('extensions_file')}")
        logger.info(f"   Компаний: {result.get('companies_count', 0)}")
        logger.info(f"   Пользователей: {result.get('users_count', 0)}")
        logger.info(f"   SIP транков: {result.get('trunks_count', 0)}")
        
        # Перезагружаем Asterisk
        logger.info("🔄 Перезагрузка Asterisk...")
        reload_result = generator.reload_asterisk()
        
        if reload_result.get('success'):
            logger.success("✅ Asterisk успешно перезагружен!")
        else:
            logger.warning(f"⚠️ Не удалось перезагрузить Asterisk: {reload_result.get('message')}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при генерации конфигов: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
