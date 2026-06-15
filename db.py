import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

def conn():
    return psycopg2.connect(DATABASE_URL)
