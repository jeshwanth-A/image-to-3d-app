import os
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

def test_db_connection():
    """Test database connection using the DATABASE_URL environment variable."""
    try:
        db_url = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
        print(f"Testing connection to database: {db_url}")
        
        # Create engine and test connection
        engine = create_engine(db_url)
        connection = engine.connect()
        connection.close()
        
        print("Database connection successful!")
        return True
    except SQLAlchemyError as e:
        print(f"Database connection error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    test_db_connection()
