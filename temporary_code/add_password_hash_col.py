def create_password_hash_col():
    c.execute("""
        ALTER TABLE users
        ADD COLUMN password_hash TEXT NOT NULL DEFAULT 0
        """)