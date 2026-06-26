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
        {"username": "admin", "password": "123", "display_name": "Admin", "role_label": "管理员", "is_admin": 1},
        {"username": "laowang", "password": "123", "display_name": "老王", "role_label": "车间工人", "is_admin": 0},
        {"username": "xiaoli", "password": "123", "display_name": "小李", "role_label": "设计师", "is_admin": 0},
    ]
    
    for u in users:
        existing = db.query(User).filter(User.username == u["username"]).first()
        if existing:
            existing.password_hash = get_password_hash(u["password"])
            existing.is_admin = u["is_admin"]
            existing.is_active = 1
            db.commit()
            new_user = existing
        else:
            new_user = User(
                username=u["username"],
                display_name=u["display_name"],
                role_label=u["role_label"],
                password_hash=get_password_hash(u["password"]),
                is_admin=u["is_admin"],
                is_active=1
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
        # Clear existing permissions for this user and re-seed
        from models import PagePermission
        db.query(PagePermission).filter(PagePermission.user_id == new_user.id).delete()
        db.commit()
        
        if new_user.is_admin == 1:
            pages = ['dashboard', 'customers', 'orders', 'process_flow', 'inventory', 'notifications', 'settings', 'outsourcing']
            for key in pages:
                perm = PagePermission(
                    user_id=new_user.id,
                    page_key=key,
                    can_view=1,
                    can_edit=1
                )
                db.add(perm)
            db.commit()
        else:
            import random
            other_pages = ['dashboard', 'customers', 'orders', 'process_flow', 'inventory', 'notifications', 'settings', 'outsourcing']
            # Randomly select a subset of other pages
            selected_pages = random.sample(other_pages, k=random.randint(3, len(other_pages)))
            for key in selected_pages:
                perm = PagePermission(
                    user_id=new_user.id,
                    page_key=key,
                    can_view=1,
                    can_edit=random.choice([0, 1])
                )
                db.add(perm)
            db.commit()
    db.close()
    print("Database seeded successfully!")

if __name__ == "__main__":
    seed_db()
