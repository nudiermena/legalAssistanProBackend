#!/usr/bin/env python3
"""
Script to check database schemas and tables
"""
import sys
import os
sys.path.append('.')

def check_database_schema():
    """Check what schemas and tables exist in the database"""
    print("🔍 CHECKING DATABASE SCHEMA")
    print("=" * 50)
    
    try:
        from postgres_memory import get_memory_instance
        
        # Get memory instance to access the database
        memory = get_memory_instance("contract_agent")
        if not memory or not memory.engine:
            print("❌ Could not get database connection")
            return
        
        print("✅ Database connection established")
        
        # Check what schemas exist
        with memory.session_factory() as session:
            try:
                from sqlalchemy import text
                
                # Get all schemas
                result = session.execute(text("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    ORDER BY schema_name
                """))
                
                schemas = [row[0] for row in result.fetchall()]
                print(f"📋 Available schemas: {schemas}")
                
                # Check for profile table in different schemas
                for schema in schemas:
                    if schema in ['information_schema', 'pg_catalog', 'pg_toast']:
                        continue  # Skip system schemas
                        
                    print(f"\n🔍 Checking schema: {schema}")
                    
                    # Check if profile table exists in this schema
                    result = session.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = :schema 
                        AND table_name = 'profile'
                    """), {'schema': schema})
                    
                    if result.fetchone():
                        print(f"✅ Profile table found in schema: {schema}")
                        
                        # Get profile table structure
                        result = session.execute(text("""
                            SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns 
                            WHERE table_schema = :schema 
                            AND table_name = 'profile'
                            ORDER BY ordinal_position
                        """), {'schema': schema})
                        
                        columns = result.fetchall()
                        print(f"   Profile table columns:")
                        for col in columns:
                            print(f"     {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
                        
                        # Get user count
                        result = session.execute(text(f"SELECT COUNT(*) FROM {schema}.profile"))
                        user_count = result.fetchone()[0]
                        print(f"   Total users: {user_count}")
                        
                        if user_count > 0:
                            # Get sample users
                            result = session.execute(text(f"""
                                SELECT id, email, full_name, created_at 
                                FROM {schema}.profile 
                                ORDER BY created_at DESC 
                                LIMIT 3
                            """))
                            
                            users = result.fetchall()
                            print(f"   Sample users:")
                            for i, user in enumerate(users):
                                print(f"     User {i+1}: ID={user[0]}, Email={user[1]}, Name={user[2]}")
                            
                            # Test contract memory storage with this user
                            if users:
                                test_user_id = users[0][0]
                                print(f"\n🎯 Testing contract memory storage with user ID: {test_user_id}")
                                
                                try:
                                    success = memory.store_contract_memory(
                                        user_id=str(test_user_id),
                                        session_id='test_session_real_user',
                                        contract_type='test_contract',
                                        analysis_summary='Test contract analysis with real user',
                                        risk_patterns=['Test risk 1', 'Test risk 2'],
                                        compliance_issues=['Test compliance 1']
                                    )
                                    
                                    if success:
                                        print("✅ Contract memory stored successfully!")
                                    else:
                                        print("⚠️  Failed to store contract memory")
                                        
                                except Exception as e:
                                    print(f"❌ Error storing contract memory: {e}")
                                    import traceback
                                    traceback.print_exc()
                        
                        break  # Found profile table, no need to check other schemas
                    else:
                        print(f"   Profile table not found in {schema}")
                        
                        # List some tables in this schema
                        result = session.execute(text("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = :schema 
                            AND table_name LIKE '%user%' OR table_name LIKE '%profile%' OR table_name LIKE '%auth%'
                            LIMIT 5
                        """), {'schema': schema})
                        
                        related_tables = [row[0] for row in result.fetchall()]
                        if related_tables:
                            print(f"   Related tables: {related_tables}")
                
            except Exception as e:
                print(f"❌ Error checking database schema: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Error during schema check: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Starting database schema check...")
    print("📁 Current directory:", os.getcwd())
    try:
        check_database_schema()
    except Exception as e:
        print(f"❌ Check failed: {str(e)}") 