#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')

from config.settings import POSTGRES_URL

def check_vector_dims():
    try:
        import psycopg
        
        # Parse the connection string properly
        conn_str = POSTGRES_URL
        if conn_str.startswith('postgresql://'):
            conn_str = conn_str.replace('postgresql://', '')
        elif conn_str.startswith('postgresql+psycopg://'):
            conn_str = conn_str.replace('postgresql+psycopg://', '')
        
        # For Supabase, parse the connection string
        if 'postgres.luiiwyzjtkqnmnzqghoz:' in conn_str:
            parts = conn_str.split('@')
            if len(parts) == 2:
                user_pass = parts[0].replace('postgres.luiiwyzjtkqnmnzqghoz:', '')
                host_port_db = parts[1]
                
                if '/' in host_port_db:
                    host_port, database = host_port_db.rsplit('/', 1)
                    if ':' in host_port:
                        host, port = host_port.split(':')
                    else:
                        host, port = host_port, '5432'
                else:
                    host, port, database = host_port_db, '5432', 'postgres'
                
                conn_str = f"host={host} port={port} dbname={database} user=postgres.luiiwyzjtkqnmnzqghoz password={user_pass}"
                print(f"Connecting to: {host}:{port}/{database}")
        
        # Connect to database
        conn = psycopg.connect(conn_str)
        cur = conn.cursor()
        
        # Check current vector dimensions
        cur.execute("SELECT vector_dims(embedding) FROM ai.document_templates WHERE embedding IS NOT NULL LIMIT 1")
        dims = cur.fetchone()
        if dims:
            print(f"Current vector dimensions: {dims[0]}")
        else:
            print("No existing embeddings found")
        
        # Check table structure
        cur.execute("""
            SELECT column_name, data_type, udt_name 
            FROM information_schema.columns 
            WHERE table_name = 'document_templates' 
            AND table_schema = 'ai' 
            AND column_name = 'embedding'
        """)
        col = cur.fetchone()
        if col:
            print(f"Embedding column: {col[0]} ({col[1]}) - UDT: {col[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking vector dimensions: {e}")

if __name__ == "__main__":
    check_vector_dims() 