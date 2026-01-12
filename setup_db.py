"""
Database setup script.
Creates all tables and seeds initial data.
"""
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

from config import get_settings
from database import Base
from models import Plan

settings = get_settings()


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
    return engine


def seed_plans(engine):
    """Seed initial SaaS plans."""
    print("\nSeeding SaaS plans...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Check if plans already exist
    existing_plans = db.query(Plan).count()
    if existing_plans > 0:
        print(f"✓ Plans already exist ({existing_plans} plans found)")
        db.close()
        return
    
    # Define plans
    plans = [
        Plan(
            name="Free",
            description="Perfect for trying out our service",
            price_monthly=Decimal("0.00"),
            price_annually=Decimal("0.00"),
            features={
                "api_calls": 1000,
                "api_keys": 1,
                "support": "community",
                "features": [
                    "1,000 API calls/month",
                    "1 API key",
                    "Community support"
                ]
            },
            active=True
        ),
        Plan(
            name="Basic",
            description="Great for individuals and small projects",
            price_monthly=Decimal("9.99"),
            price_annually=Decimal("99.00"),
            features={
                "api_calls": 10000,
                "api_keys": 3,
                "support": "email",
                "features": [
                    "10,000 API calls/month",
                    "3 API keys",
                    "Email support",
                    "Priority processing"
                ]
            },
            active=True
        ),
        Plan(
            name="Pro",
            description="For growing businesses and teams",
            price_monthly=Decimal("29.99"),
            price_annually=Decimal("299.00"),
            features={
                "api_calls": 100000,
                "api_keys": 10,
                "support": "priority",
                "features": [
                    "100,000 API calls/month",
                    "10 API keys",
                    "Priority support",
                    "Advanced analytics",
                    "Custom integrations"
                ]
            },
            active=True
        ),
        Plan(
            name="Enterprise",
            description="Custom solutions for large organizations",
            price_monthly=Decimal("99.99"),
            price_annually=Decimal("999.00"),
            features={
                "api_calls": -1,  # Unlimited
                "api_keys": -1,  # Unlimited
                "support": "dedicated",
                "features": [
                    "Unlimited API calls",
                    "Unlimited API keys",
                    "Dedicated support",
                    "Custom SLA",
                    "On-premise deployment option",
                    "Advanced security features"
                ]
            },
            active=True
        )
    ]
    
    # Add plans to database
    for plan in plans:
        db.add(plan)
        print(f"  ✓ Created plan: {plan.name}")
    
    db.commit()
    db.close()
    print("✓ Plans seeded successfully")


def main():
    """Main setup function."""
    print("=" * 60)
    print("FastAPI + Supabase Auth - Database Setup")
    print("=" * 60)
    
    try:
        # Create tables
        engine = create_tables()
        
        # Seed plans
        seed_plans(engine)
        
        print("\n" + "=" * 60)
        print("✓ Database setup completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Configure your .env file with Supabase credentials")
        print("2. Run the application: uvicorn main:app --reload")
        print("3. Visit http://localhost:8000/docs for API documentation")
        
    except Exception as e:
        print(f"\n✗ Error during setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
