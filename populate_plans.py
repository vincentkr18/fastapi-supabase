
"""
Script to populate plans table with Dodo payment product IDs
"""
import asyncio
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Plan, Base
import uuid

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)


def populate_plans():
    """Populate the plans table with pricing data"""
    db = SessionLocal()
    
    try:
        # Define plans data
        plans_data = [
            {
                "name": "Starter",
                "description": "Perfect for individuals getting started",
                "pricing": {
                    "monthly_usd": 90.00,
                    "annual_usd": 961.00
                },
                "provider_ids": {
                    "dodo_monthly": "pdt_0NWhfnZ7Iw3iCCKCeTBJp",
                    "dodo_annual": "pdt_0NWhgfSKhkjegVdQH7Qo7"
                },
                "features": {
                    "api_calls": 10000,
                    "storage_gb": 50,
                    "team_members": 1,
                    "support": "email"
                }
            },
            {
                "name": "Creator",
                "description": "Ideal for content creators and small teams",
                "pricing": {
                    "monthly_usd": 180.00,
                    "annual_usd": 1920.00
                },
                "provider_ids": {
                    "dodo_monthly": "pdt_0NWhg1XVar7kI7iyYtaIH",
                    "dodo_annual": "pdt_0NWhgnOcVYsmRppZuqVKn"
                },
                "features": {
                    "api_calls": 50000,
                    "storage_gb": 200,
                    "team_members": 5,
                    "support": "priority_email"
                }
            },
            {
                "name": "Pro",
                "description": "For professionals and growing businesses",
                "pricing": {
                    "monthly_usd": 450.00,
                    "annual_usd": 4799.00
                },
                "provider_ids": {
                    "dodo_monthly": "pdt_0NWhgD09OqDnfjW7u0SfC",
                    "dodo_annual": "pdt_0NWhgsgQBxyMNfpws0yxR"
                },
                "features": {
                    "api_calls": 200000,
                    "storage_gb": 1000,
                    "team_members": 20,
                    "support": "24/7_priority"
                }
            }
        ]
        
        # Check if plans already exist
        existing_plans = db.query(Plan).all()
        if existing_plans:
            print(f"Found {len(existing_plans)} existing plans.")
            overwrite = input("Do you want to delete and recreate all plans? (yes/no): ")
            if overwrite.lower() == 'yes':
                db.query(Plan).delete()
                db.commit()
                print("Existing plans deleted.")
            else:
                print("Keeping existing plans. Exiting.")
                return
        
        # Create plans
        created_plans = []
        for plan_data in plans_data:
            plan = Plan(
                id=uuid.uuid4(),
                name=plan_data["name"],
                description=plan_data["description"],
                pricing=plan_data["pricing"],
                provider_ids=plan_data["provider_ids"],
                features=plan_data["features"],
                is_active=True
            )
            db.add(plan)
            created_plans.append(plan)
            print(f"✓ Created plan: {plan.name}")
            print(f"  - Monthly: ${plan.pricing['monthly_usd']} (ID: {plan.provider_ids['dodo_monthly']})")
            print(f"  - Annual: ${plan.pricing['annual_usd']} (ID: {plan.provider_ids['dodo_annual']})")
        
        # Commit to database
        db.commit()
        
        print(f"\n✅ Successfully created {len(created_plans)} plans!")
        
        # Display summary
        print("\n" + "="*60)
        print("PLANS SUMMARY")
        print("="*60)
        for plan in created_plans:
            print(f"\n{plan.name} (ID: {plan.id})")
            print(f"  Monthly: ${plan.pricing['monthly_usd']}")
            print(f"  Annual: ${plan.pricing['annual_usd']}")
            print(f"  Dodo Monthly ID: {plan.provider_ids['dodo_monthly']}")
            print(f"  Dodo Annual ID: {plan.provider_ids['dodo_annual']}")
            print(f"  Features: {plan.features}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        db.close()

# Add a default 'basic' plan with $0 if not present
from models import Plan
from database import get_db
from sqlalchemy.orm import Session

def add_basic_plan():
    db: Session = next(get_db())
    basic_plan = db.query(Plan).filter(Plan.name == "basic").first()
    if not basic_plan:
        plan = Plan(
            id=uuid.uuid4(),
            name="Basic",
            description="Default free plan",
            pricing={"monthly_usd": 0, "annual_usd": 0},
            provider_ids={"dodo_monthly": "", "dodo_annual": ""},
            features={},
            is_active=True
        )
        db.add(plan)
        db.commit()
        
        print("Added default 'basic' plan.")
        print(f"\n{plan.name} (ID: {plan.id})")
    else:
        print("'basic' plan already exists.")

    
def delete_all_plans():
    db: Session = next(get_db())
    deleted = db.query(Plan).delete()
    db.commit()
    print(f"Deleted {deleted} plans from the table.")



if __name__ == "__main__":
    print("Deleteing plan population...")
    print("="*60)
    delete_all_plans()
    print("Starting new plan population...")
    print("="*60)
    populate_plans()
    add_basic_plan()
