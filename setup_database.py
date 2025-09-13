#!/usr/bin/env python3
"""
Setup database schema for Legal AI Assistant
"""

import os
import asyncio
from supabase import create_client, Client

async def setup_database():
    """Setup the database schema"""
    try:
        # Get environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        print(f"Setting up database schema...")
        print(f"Supabase URL: {supabase_url}")
        
        if not supabase_url or not supabase_key:
            print("ERROR: Missing Supabase environment variables")
            return False
        
        # Create client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Read the schema file
        schema_file = "knowledge_base_schema.sql"
        if not os.path.exists(schema_file):
            print(f"ERROR: Schema file {schema_file} not found")
            return False
        
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        print("Schema file loaded successfully")
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        print(f"Found {len(statements)} SQL statements to execute")
        
        # Execute each statement
        for i, statement in enumerate(statements, 1):
            if statement and not statement.startswith('--'):
                try:
                    print(f"Executing statement {i}/{len(statements)}...")
                    # Note: Supabase doesn't support direct SQL execution via RPC
                    # You'll need to run this in the Supabase SQL editor
                    print(f"SQL: {statement[:100]}...")
                except Exception as e:
                    print(f"Error executing statement {i}: {e}")
        
        print("\n" + "="*50)
        print("DATABASE SETUP INSTRUCTIONS:")
        print("="*50)
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the contents of knowledge_base_schema.sql")
        print("4. Execute the SQL")
        print("5. Verify tables are created")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(setup_database()) 