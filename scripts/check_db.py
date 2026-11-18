import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from sqlalchemy import create_engine, inspect, text
    from app.core.config import settings
    
    print(f"Checking DB at: {settings.SQLALCHEMY_DATABASE_URI}")
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    
    with engine.connect() as connection:
        print("Successfully connected to Database!")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables found ({len(tables)}):", tables)
        
        if len(tables) == 0:
            print("ERROR: Database has NO tables. Migration required.")
        else:
            print("Database setup looks correct.")
            
except Exception as e:
    print("Connection Failed:", e)
