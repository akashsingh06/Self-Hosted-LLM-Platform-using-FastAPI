#!/usr/bin/env python3
import sqlite3

print("Testing database...")

try:
    conn = sqlite3.connect("llm_platform.db")
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print(f"✅ Found {len(tables)} tables:")
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print(f"  • {table[0]} ({len(columns)} columns)")
    
    # Test user
    cursor.execute("SELECT username, email, is_admin FROM users")
    users = cursor.fetchall()
    print(f"\n👤 Users: {len(users)}")
    for user in users:
        print(f"  • {user[0]} ({user[1]}) - Admin: {user[2]}")
    
    conn.close()
    print("\n🎉 Database is ready!")
    
except Exception as e:
    print(f"❌ Error: {e}")