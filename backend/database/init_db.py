"""
Database Schema Initializer and Baseline Seed Script.
"""
from backend.database.connection import engine, Base, SessionLocal
from backend.database.models import User, Project
from backend.services.auth_service import hash_password

def init_db():
    """Initializes all SQL database tables and seeds baseline admin if not existing."""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Seed default admin user
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=hash_password("admin123"),
                display_name="Lead QA Administrator",
                email="admin@telecos.com.au",
                role="admin",
                is_admin=True
            )
            db.add(admin)

        # Seed baseline project H8097
        h8097 = db.query(Project).filter(Project.id == "H8097").first()
        if not h8097:
            h8097 = Project(
                id="H8097",
                name="AUSTINS FERRY",
                code="H8097",
                structure_type="CONCRETE MONOPOLE (26.8m)",
                drawing_revision="FOR CONSTRUCTION (Rev 1.0)",
                primary_drawing="H8097_AUSTINS FERRY_FC_05122025_Final PDF After QC validation.pdf"
            )
            db.add(h8097)

        db.commit()
    except Exception as e:
        db.rollback()
        print("Database seed exception:", e)
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database schema successfully initialized.")
