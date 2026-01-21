import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client with service role key (has admin privileges)
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Important: use service role, not anon key
)

def create_trigger():
    """
    Creates a database trigger to automatically assign Basic plan to new users.
    """
    
    # SQL for the trigger function
    trigger_sql = """
    -- Function to get Basic plan ID
    CREATE OR REPLACE FUNCTION get_basic_plan_id()
    RETURNS UUID AS $$
    DECLARE
        basic_plan_id UUID;
    BEGIN
        SELECT id INTO basic_plan_id
        FROM plans
        WHERE LOWER(name) = 'basic'
        AND is_active = true
        LIMIT 1;
        
        RETURN basic_plan_id;
    END;
    $$ LANGUAGE plpgsql;

    -- Trigger function
    CREATE OR REPLACE FUNCTION create_default_subscription()
    RETURNS TRIGGER AS $$
    DECLARE
        basic_plan_id UUID;
        profile_id UUID;
    BEGIN
        -- Get the Basic plan ID
        basic_plan_id := get_basic_plan_id();
        
        IF basic_plan_id IS NULL THEN
            RAISE WARNING 'No Basic plan found for user %', NEW.id;
            RETURN NEW;
        END IF;
        
        profile_id := NEW.id;
        
        -- Check if subscription exists
        IF NOT EXISTS (
            SELECT 1 FROM subscriptions WHERE user_id = profile_id
        ) THEN
            INSERT INTO subscriptions (
                id,
                user_id,
                plan_id,
                provider,
                provider_subscription_id,
                status,
                current_period_start,
                current_period_end,
                cancel_at_period_end,
                event_log,
                created_at,
                updated_at
            ) VALUES (
                gen_random_uuid(),
                profile_id,
                basic_plan_id,
                'internal',
                'free_' || profile_id::text,
                'active',
                NOW(),
                NOW() + INTERVAL '100 years',
                false,
                jsonb_build_array(
                    jsonb_build_object(
                        'event', 'created',
                        'date', NOW(),
                        'metadata', jsonb_build_object(
                            'source', 'auto_signup',
                            'plan', 'basic'
                        )
                    )
                ),
                NOW(),
                NOW()
            );
        END IF;
        
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;

    -- Create trigger
    DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
    CREATE TRIGGER on_auth_user_created
        AFTER INSERT ON auth.users
        FOR EACH ROW
        EXECUTE FUNCTION create_default_subscription();
    """
    
    try:
        # Execute the SQL using Supabase RPC
        result = supabase.rpc('exec_sql', {'query': trigger_sql}).execute()
        print("✅ Trigger created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating trigger: {e}")
        print("\n💡 Alternative: Run the SQL directly in Supabase SQL Editor")
        return False


def backfill_existing_users():
    """
    Backfill subscriptions for existing users who don't have one.
    """
    try:
        # Get Basic plan
        plan_response = supabase.table("plans")\
            .select("id")\
            .eq("name", "Basic")\
            .eq("is_active", True)\
            .limit(1)\
            .execute()
        
        if not plan_response.data:
            print("❌ No Basic plan found!")
            return
        
        basic_plan_id = plan_response.data[0]["id"]
        print(f"✅ Found Basic plan: {basic_plan_id}")
        
        # Get all users from profiles
        profiles_response = supabase.table("profiles")\
            .select("id")\
            .execute()
        
        if not profiles_response.data:
            print("ℹ️ No profiles found")
            return
        
        print(f"📊 Found {len(profiles_response.data)} profiles")
        
        # Check which users don't have subscriptions
        created_count = 0
        for profile in profiles_response.data:
            user_id = profile["id"]
            
            # Check if subscription exists
            sub_response = supabase.table("subscriptions")\
                .select("id")\
                .eq("user_id", user_id)\
                .execute()
            
            if not sub_response.data:
                # Create subscription
                from datetime import datetime, timedelta
                
                subscription_data = {
                    "user_id": user_id,
                    "plan_id": basic_plan_id,
                    "provider": "internal",
                    "provider_subscription_id": f"free_{user_id}",
                    "status": "active",
                    "current_period_start": datetime.utcnow().isoformat(),
                    "current_period_end": (datetime.utcnow() + timedelta(days=36500)).isoformat(),
                    "cancel_at_period_end": False,
                    "event_log": [
                        {
                            "event": "created",
                            "date": datetime.utcnow().isoformat(),
                            "metadata": {
                                "source": "backfill",
                                "plan": "basic"
                            }
                        }
                    ]
                }
                
                supabase.table("subscriptions").insert(subscription_data).execute()
                created_count += 1
                print(f"✅ Created subscription for user: {user_id}")
        
        print(f"\n🎉 Backfill complete! Created {created_count} subscriptions")
        
    except Exception as e:
        print(f"❌ Error during backfill: {e}")


if __name__ == "__main__":
    print("🚀 Setting up automatic subscription creation...")
    print("\n" + "="*60)
    
    # Note: Direct SQL execution might not work via Supabase client
    # You'll likely need to run the SQL in Supabase SQL Editor
    print("\n📝 Step 1: Copy and run the SQL trigger in Supabase SQL Editor")
    print("="*60)
    
    trigger_created = create_trigger()
    
    if not trigger_created:
        print("\n⚠️  Please run the trigger SQL manually in Supabase SQL Editor")
        print("   Dashboard > SQL Editor > New query > Paste the SQL above")
    
    print("\n" + "="*60)
    print("\n📝 Step 2: Backfill existing users")
    print("="*60)
    
    backfill = input("\nBackfill subscriptions for existing users? (y/n): ")
    if backfill.lower() == 'y':
        backfill_existing_users()
    
    print("\n✅ Setup complete!")