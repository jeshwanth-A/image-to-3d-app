from app import app, db, User
import os

def init_db():
    print("Initializing database...")
    try:
        with app.app_context():
            # Create tables
            db.create_all()
            
            # Check if admin user exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', is_admin=True)
                admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin'))
                db.session.add(admin)
                db.session.commit()
                print("Admin user created.")
            else:
                print("Admin user already exists.")
                
        print("Database initialization complete.")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")

if __name__ == '__main__':
    init_db()
