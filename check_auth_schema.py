#!/usr/bin/env python3
"""
Script to check what tables exist in the auth schema
"""
import sys
import os
sys.path.append('.')

def check_auth_schema():
    """Check what tables exist in the auth schema"""
    print("🔍 CHECKING AUTH SCHEMA TABLES")
    print("=" * 50)
    
    try:
        from postgres_memory import get_memory_instance
        
        # Get memory instance to access the database
        memory = get_memory_instance("contract_agent")
        if not memory or not memory.engine:
            print("❌ Could not get database connection")
            return
        
        print("✅ Database connection established")
        
        # Check what tables exist in auth schema
        with memory.session_factory() as session:
            try:
                from sqlalchemy import text
                
                # Get all tables in auth schema
                result = session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'auth' 
                    ORDER BY table_name
                """))
                
                auth_tables = [row[0] for row in result.fetchall()]
                print(f"📋 Tables in auth schema: {auth_tables}")
                
                # Check each table for user-related data
                for table_name in auth_tables:
                    print(f"\n🔍 Checking table: auth.{table_name}")
                    
                    try:
                        # Get table structure
                        result = session.execute(text("""
                            SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns 
                            WHERE table_schema = 'auth' 
                            AND table_name = :table_name
                            ORDER BY ordinal_position
                        """), {'table_name': table_name})
                        
                        columns = result.fetchall()
                        print(f"   Columns:")
                        for col in columns:
                            print(f"     {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
                        
                        # Check if this table has user data
                        if any('id' in col[0].lower() for col in columns):
                            try:
                                result = session.execute(text(f"SELECT COUNT(*) FROM auth.{table_name}"))
                                row_count = result.fetchone()[0]
                                print(f"   Row count: {row_count}")
                                
                                if row_count > 0:
                                    # Get sample data
                                    result = session.execute(text(f"SELECT * FROM auth.{table_name} LIMIT 2"))
                                    sample_rows = result.fetchall()
                                    print(f"   Sample data:")
                                    for i, row in enumerate(sample_rows):
                                        print(f"     Row {i+1}: {row}")
                                        
                            except Exception as e:
                                print(f"   Error querying table: {e}")
                                
                    except Exception as e:
                        print(f"   Error getting table structure: {e}")
                
            except Exception as e:
                print(f"❌ Error checking auth schema: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Error during auth schema check: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 Starting auth schema check...")
    print("📁 Current directory:", os.getcwd())
    try:
        check_auth_schema()
    except Exception as e:
        print(f"❌ Check failed: {str(e)}")


