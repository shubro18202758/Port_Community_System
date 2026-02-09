"""Test imports for SmartBerth AI Service"""
import sys
print("Testing imports...")

try:
    from config import get_settings
    print("✅ config.py")
except Exception as e:
    print(f"❌ config.py: {e}")
    sys.exit(1)

try:
    from database import get_db_service
    print("✅ database.py")
except Exception as e:
    print(f"❌ database.py: {e}")
    sys.exit(1)

try:
    from model import get_model
    print("✅ model.py")
except Exception as e:
    print(f"❌ model.py: {e}")
    sys.exit(1)

try:
    from services import get_eta_predictor, get_berth_allocator, get_constraint_validator
    print("✅ services.py")
except Exception as e:
    print(f"❌ services.py: {e}")
    sys.exit(1)

try:
    from rag import get_rag_pipeline
    print("✅ rag.py")
except Exception as e:
    print(f"❌ rag.py: {e}")
    sys.exit(1)

try:
    from chatbot import get_chatbot
    print("✅ chatbot.py")
except Exception as e:
    print(f"❌ chatbot.py: {e}")
    sys.exit(1)

try:
    import main
    print("✅ main.py")
except Exception as e:
    print(f"❌ main.py: {e}")
    sys.exit(1)

print("\n✅ All imports successful!")

# Test database connection
settings = get_settings()
print(f"\nModel: {settings.model_name}")
print(f"Database: {settings.db_server}/{settings.db_name}")

db = get_db_service()
if db.test_connection():
    print("✅ Database connection successful")
else:
    print("❌ Database connection failed")
