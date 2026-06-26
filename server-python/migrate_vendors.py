import os
from sqlalchemy import text
from database import engine

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE vendors ADD COLUMN contact_methods JSON DEFAULT '[]'::json;"))
        conn.commit()
        print("Successfully added contact_methods to vendors table.")
    except Exception as e:
        print("Error or already exists:", e)
