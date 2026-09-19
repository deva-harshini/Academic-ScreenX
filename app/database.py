from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# SQLite configuration
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Database session dependency with automatic table verification"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Ensure all database tables and default faculty user exist across local and serverless environments"""
    try:
        import app.models  # Populate Base.metadata
        Base.metadata.create_all(bind=engine)
        
        # Ensure new RAG columns exist on older SQLite databases
        try:
            with engine.connect() as conn:
                inspector = inspect(engine)
                if "submissions" in inspector.get_table_names():
                    cols = [c["name"] for c in inspector.get_columns("submissions")]
                    if "rag_evaluation" not in cols:
                        conn.execute(text("ALTER TABLE submissions ADD COLUMN rag_evaluation TEXT DEFAULT '{}'"))
                    if "rag_match_status" not in cols:
                        conn.execute(text("ALTER TABLE submissions ADD COLUMN rag_match_status VARCHAR(50)"))
                    if "rag_evidence" not in cols:
                        conn.execute(text("ALTER TABLE submissions ADD COLUMN rag_evidence TEXT DEFAULT '[]'"))
                    if "rag_missing_requirements" not in cols:
                        conn.execute(text("ALTER TABLE submissions ADD COLUMN rag_missing_requirements TEXT DEFAULT '[]'"))
                    conn.commit()
        except Exception:
            pass

        # Seed default faculty user if not exists
        db = SessionLocal()
        try:
            from app.models import User, UserRole
            import bcrypt
            
            default_email = "faculty@university.edu"
            existing = db.query(User).filter(User.email == default_email).first()
            salt = bcrypt.gensalt()
            pw_hash = bcrypt.hashpw(b"ASX_Faculty#2026!Pass", salt).decode("utf-8")
            if not existing:
                faculty_user = User(
                    email=default_email,
                    name="Dr. Eleanor Vance (Faculty Chair)",
                    password_hash=pw_hash,
                    role=UserRole.FACULTY.value
                )
                db.add(faculty_user)
                db.commit()
            else:
                existing.password_hash = pw_hash
                db.commit()
        finally:
            db.close()
    except Exception as e:
        import logging
        logging.getLogger("AcademicScreenX").error(f"Database initialization error: {e}", exc_info=True)

# Run initialization on import
init_db()
