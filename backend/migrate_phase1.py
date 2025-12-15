#!/usr/bin/env python3
"""
Test script to verify Phase 1 database changes.
Run this to check that the new columns and tables exist.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import engine, test_connection
from sqlalchemy import text, inspect

def check_schema():
    """Check that all new schema changes exist."""
    print("\n" + "=" * 60)
    print("   PHASE 1: DATABASE SCHEMA VERIFICATION")
    print("=" * 60 + "\n")
    
    # Test connection
    if not test_connection():
        return False
    
    inspector = inspect(engine)
    
    # Check user_settings columns
    print("\n📋 Checking user_settings table...")
    user_settings_cols = {col['name'] for col in inspector.get_columns('user_settings')}
    required_cols = ['max_items_per_category', 'target_word_count', 'sources']
    
    for col in required_cols:
        if col in user_settings_cols:
            print(f"   ✅ {col}")
        else:
            print(f"   ❌ {col} - MISSING")
            return False
    
    # Check email_delivery_logs table exists
    print("\n📋 Checking email_delivery_logs table...")
    tables = inspector.get_table_names()
    
    if 'email_delivery_logs' in tables:
        print("   ✅ email_delivery_logs table exists")
        
        # Check columns
        delivery_cols = {col['name'] for col in inspector.get_columns('email_delivery_logs')}
        required_delivery_cols = [
            'id', 'user_id', 'delivered_at', 'categories_used', 'items_per_category',
            'word_count_target', 'actual_word_count', 'feedback_token', 'feedback_received'
        ]
        
        for col in required_delivery_cols:
            if col in delivery_cols:
                print(f"   ✅ {col}")
            else:
                print(f"   ❌ {col} - MISSING")
                return False
    else:
        print("   ❌ email_delivery_logs table - MISSING")
        return False
    
    print("\n" + "=" * 60)
    print("   ✅ ALL PHASE 1 SCHEMA CHECKS PASSED!")
    print("=" * 60 + "\n")
    return True


def apply_migration():
    """Apply schema changes to existing database."""
    print("\n🔧 Applying schema migration...")
    
    with engine.connect() as conn:
        # Add new columns to user_settings if they don't exist
        try:
            conn.execute(text("""
                ALTER TABLE user_settings 
                ADD COLUMN IF NOT EXISTS max_items_per_category INTEGER DEFAULT 5
            """))
            conn.execute(text("""
                ALTER TABLE user_settings 
                ADD COLUMN IF NOT EXISTS target_word_count INTEGER DEFAULT 500
            """))
            conn.execute(text("""
                ALTER TABLE user_settings 
                ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT '[]'::jsonb
            """))
            conn.commit()
            print("   ✅ user_settings columns added")
        except Exception as e:
            print(f"   ⚠️ user_settings columns: {e}")
        
        # Create email_delivery_logs table
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS email_delivery_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    delivered_at TIMESTAMPTZ DEFAULT NOW(),
                    categories_used JSONB,
                    sources_used JSONB,
                    items_per_category INTEGER,
                    word_count_target INTEGER,
                    actual_word_count INTEGER,
                    email_sent_to VARCHAR(255),
                    pdf_included BOOLEAN DEFAULT TRUE,
                    audio_included BOOLEAN DEFAULT FALSE,
                    feedback_token VARCHAR(64) UNIQUE,
                    feedback_expires_at TIMESTAMPTZ,
                    feedback_received VARCHAR(20),
                    feedback_received_at TIMESTAMPTZ
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_email_delivery_logs_user_id 
                ON email_delivery_logs(user_id)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_email_delivery_logs_feedback_token 
                ON email_delivery_logs(feedback_token)
            """))
            conn.commit()
            print("   ✅ email_delivery_logs table created")
        except Exception as e:
            print(f"   ⚠️ email_delivery_logs: {e}")
    
    print("   ✅ Migration complete!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Phase 1 database migration")
    parser.add_argument("--apply", action="store_true", help="Apply migrations")
    parser.add_argument("--check", action="store_true", help="Check schema only")
    args = parser.parse_args()
    
    if args.apply:
        apply_migration()
    
    if args.check or not args.apply:
        success = check_schema()
        sys.exit(0 if success else 1)
