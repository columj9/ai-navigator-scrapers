import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not found in .env file")
        return

    conn = None
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        cur.execute("SELECT NOW();")
        time = cur.fetchone()
        print(f"Successfully connected to database. Current time: {time[0]}")
        cur.close()
    except (Exception, psycopg2.Error) as error:
        print(f"Error while connecting to PostgreSQL: {error}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    test_connection() 