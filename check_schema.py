#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')

from config.settings import POSTGRES_URL

def check_schema():
    try:
        import psycopg
        
        # Parse the connection string properly
        conn_str = POSTGRES_URL
        if conn_str.startswith('postgresql://'):
            conn_str = conn_str.replace('postgresql://', '')
        elif conn_str.startswith('postgresql+psycopg://'):
            conn_str = conn_str.replace('postgresql+psycopg://', '')
        
        print(f"Connection string: {conn_str}")
        
        # For Supabase, we need to parse the connection string properly
        # Format: postgres.luiiwyzjtkqnmnzqghoz:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
        if 'postgres.luiiwyzjtkqnmnzqghoz:' in conn_str:
            # Extract components
            parts = conn_str.split('@')
            if len(parts) == 2:
                user_pass = parts[0].replace('postgres.luiiwyzjtkqnmnzqghoz:', '')
                host_port_db = parts[1]
                
                # Parse host:port/database
                if '/' in host_port_db:
                    host_port, database = host_port_db.rsplit('/', 1)
                    if ':' in host_port:
                        host, port = host_port.split(':')
                    else:
                        host, port = host_port, '5432'
                else:
                    host, port, database = host_port_db, '5432', 'postgres'
                
                # Build proper connection string
                conn_str = f"host={host} port={port} dbname={database} user=postgres.luiiwyzjtkqnmnzqghoz password={user_pass}"
                print(f"Parsed connection: host={host} port={port} dbname={database}")
        
        # Connect to database
        conn = psycopg.connect(conn_str)
        cur = conn.cursor()
        
        # Check table schema
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'document_templates' 
            AND table_schema = 'ai' 
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        print("\nTable schema for ai.document_templates:")
        for col in columns:
            print(f"  {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
        
        # Check if table exists and has data
        cur.execute("SELECT COUNT(*) FROM ai.document_templates")
        count = cur.fetchone()[0]
        print(f"\nCurrent row count: {count}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    check_schema() 