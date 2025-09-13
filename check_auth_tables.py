#!/usr/bin/env python3
"""
Check auth tables structure and existing users
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_auth_tables():
    """Check auth tables structure and existing users"""
    try:
        from config.settings import POSTGRES_URL
        from sqlalchemy import create_engine, text
        
        logger.info("🔍 Checking auth tables structure...")
        
        engine = create_engine(POSTGRES_URL)
        with engine.connect() as conn:
            # Check if auth.users table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'auth' 
                ORDER BY table_name
            """))
            auth_tables = [row[0] for row in result.fetchall()]
            logger.info(f"📊 Auth tables: {auth_tables}")
            
            # Check auth.users structure
            if 'users' in auth_tables:
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'auth' AND table_name = 'users'
                    ORDER BY ordinal_position
                """))
                users_columns = result.fetchall()
                logger.info("📋 Auth.users table structure:")
                for col in users_columns:
                    logger.info(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
                
                # Check users count
                result = conn.execute(text("SELECT COUNT(*) FROM auth.users"))
                users_count = result.fetchone()[0]
                logger.info(f"👥 Total users in auth.users: {users_count}")
                
                # Show some users
                if users_count > 0:
                    result = conn.execute(text("""
                        SELECT id, email, created_at, updated_at 
                        FROM auth.users 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """))
                    users = result.fetchall()
                    logger.info("👤 Recent users:")
                    for user in users:
                        logger.info(f"  - ID: {user[0]}, Email: {user[1]}, Created: {user[2]}")
            
            # Check if profiles table exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'profiles'
            """))
            profiles_exists = result.fetchone() is not None
            logger.info(f"📊 Profiles table exists: {profiles_exists}")
            
            if profiles_exists:
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = 'profiles'
                    ORDER BY ordinal_position
                """))
                profiles_columns = result.fetchall()
                logger.info("📋 Profiles table structure:")
                for col in profiles_columns:
                    logger.info(f"  - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
                
                # Check profiles count
                result = conn.execute(text("SELECT COUNT(*) FROM profiles"))
                profiles_count = result.fetchone()[0]
                logger.info(f"👥 Total profiles: {profiles_count}")
                
                if profiles_count > 0:
                    result = conn.execute(text("""
                        SELECT id, email, username, full_name, created_at 
                        FROM profiles 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """))
                    profiles = result.fetchall()
                    logger.info("👤 Recent profiles:")
                    for profile in profiles:
                        logger.info(f"  - ID: {profile[0]}, Email: {profile[1]}, Username: {profile[2]}, Name: {profile[3]}")
            
            # Check ai schema tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'ai' 
                ORDER BY table_name
            """))
            ai_tables = [row[0] for row in result.fetchall()]
            logger.info(f"📊 AI tables: {ai_tables}")
            
            # Check foreign key constraints
            result = conn.execute(text("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' 
                  AND tc.table_schema = 'ai'
                ORDER BY tc.table_name, kcu.column_name
            """))
            foreign_keys = result.fetchall()
            logger.info("🔗 Foreign key constraints in ai schema:")
            for fk in foreign_keys:
                logger.info(f"  - {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]}")
            
    except Exception as e:
        logger.error(f"❌ Error checking auth tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_auth_tables() 