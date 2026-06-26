import os
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from models import User
import bcrypt

def get_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    users = [
        {"username": "admin", "password": "admin123", "display_name": "Admin", "role_label": "管理员", "is_admin": 1},
        {"username": "laowang", "password": "123456", "display_name": "老王", "role_label": "车间工人", "is_admin": 0},
        {"username": "xiaoli", "password": "123456", "display_name": "小李", "role_label": "设计师", "is_admin": 0},
    ]
    
    for u in users:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if not existing:
            new_user = User(
                username=u["username"],
                display_name=u["display_name"],
                role_label=u["role_label"],
                password_hash=get_password_hash(u["password"]),
                is_admin=u["is_admin"]
            )
            db.add(new_user)
    
    db.commit()
    db.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_db()
