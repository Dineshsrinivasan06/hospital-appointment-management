
import sqlite3

DB_PATH = "doctor_appointments.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(admins)")
    columns = [row[1] for row in cursor.fetchall()]

    print("Existing columns:", columns)

    if "password_hash" in columns:
        cursor.execute("""
            UPDATE admins
            SET password_hash = ''
            WHERE password_hash IS NULL
        """)

        cursor.execute("""
            UPDATE admins
            SET password_hash = hashed_password
            WHERE password_hash = ''
            AND hashed_password IS NOT NULL
        """)

        cursor.execute("""
            UPDATE admins
            SET password_hash = ''
            WHERE password_hash IS NULL
        """)

        # Remove NOT NULL constraint by rebuilding the table
        cursor.execute("""
            CREATE TABLE admins_new (
                id INTEGER PRIMARY KEY,
                username VARCHAR NOT NULL UNIQUE,
                email VARCHAR UNIQUE,
                hashed_password VARCHAR NOT NULL
            )
        """)

        cursor.execute("""
            INSERT INTO admins_new
                (id, username, email, hashed_password)
            SELECT
                id,
                username,
                email,
                COALESCE(
                    NULLIF(hashed_password, ''),
                    password_hash
                )
            FROM admins
        """)

        cursor.execute("DROP TABLE admins")
        cursor.execute("ALTER TABLE admins_new RENAME TO admins")

    conn.commit()
    print("Admin database migration completed!")

except Exception as e:
    conn.rollback()
    print("Migration error:", repr(e))

finally:
    conn.close()
