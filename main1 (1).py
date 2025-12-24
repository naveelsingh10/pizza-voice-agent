import os
import json
import secrets
import signal
import sys
import warnings
import time  # Moved to top for better access
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ClientTools
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ['LIBASOUND_THREAD_SAFE'] = '0'

# --- CONFIGURATION ---
AGENT_ID = "agent_8101kd5d5c3ffpbb9sqrzrm9htsy"
API_KEY = "sk_66f0aea5b12ee6c4587e00c381cb0d11be7ca5f1e8d91ee5"

# --- 1. SETUP TOOLS ---
client_tools = ClientTools()

def get_order_status(params):
    """Get order status with improved error handling"""
    order_id = str(params.get("order_id", "")).strip()
    
    if not order_id:
        print("\n❌ [Tool] No order ID provided")
        return "I need an order number to check the status. Could you please provide your order number?"
    
    print(f"\n🔍 [Tool] Looking up Order: {order_id}")

    try:
        # Check if orders.json exists
        if not os.path.exists("orders.json"):
            print("   ❌ Database file missing")
            return "I'm unable to access the order system right now. Please try again in a moment."
        
        with open("orders.json", "r") as file:
            orders = json.load(file)

        status = orders.get(order_id)

        if status:
            print(f"   ✅ Status: {status}")
            
            # Format response based on status
            if status.lower() == "delayed":
                return f"Order {order_id} is delayed. I apologize for the inconvenience."
            elif status.lower() == "delivered":
                return f"Order {order_id} has been delivered!"
            elif status.lower() == "out for delivery":
                return f"Order {order_id} is out for delivery and should arrive soon."
            elif status.lower() == "preparing":
                return f"Order {order_id} is being prepared in our kitchen."
            else:
                return f"Order {order_id} status is {status}."
        else:
            print(f"   ❌ Not found")
            return f"I couldn't find order {order_id} in our system. Please double-check the order number."
            
    except json.JSONDecodeError:
        print("   ❌ Invalid database format")
        return "There's an issue with our order system. Please contact support."
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return "I'm having trouble checking that order. Please try again."

def generate_discount(params):
    """Generate a clean, readable discount code"""
    # Use format: PIZZA5-XXXXXX (6 alphanumeric characters)
    code_suffix = secrets.token_hex(3).upper()  # Generates 6 hex chars
    new_code = f"PIZZA5-{code_suffix}"
    
    print(f"\n💰 [Tool] Generated Discount Code: {new_code}")
    
    # Return in a format that's easy to read aloud
    return f"Your discount code is {new_code}. That's PIZZA, the number 5, dash, {code_suffix}. You can use this for 5 dollars off your next order."

# Register tools
client_tools.register("get_order_status", get_order_status)
client_tools.register("generate_discount", generate_discount)

# --- 2. MAIN CONVERSATION LOOP ---
def main():
    if not API_KEY or "YOUR_ACTUAL_API" in API_KEY:
        print("❌ ERROR: Please set your API_KEY and AGENT_ID.")
        return

    print("🔧 Initializing Pizza Agent...")
    
    # Verify orders.json exists
    if not os.path.exists("orders.json"):
        print("⚠️  orders.json not found. Creating default file...")
        default_orders = {
            "1234": "Delivered",
            "5678": "Out for delivery",
            "9999": "Delayed",
            "1111": "Preparing"
        }
        with open("orders.json", "w") as f:
            json.dump(default_orders, f, indent=2)
        print("✅ Created orders.json")
    
    try:
        client = ElevenLabs(api_key=API_KEY)
        audio_interface = DefaultAudioInterface()

        # Session management
        session_active = {'active': False}
        
        # --- NEW: Function to detect "Goodbye" and exit ---
        def handle_agent_response(response):
            print(f"🤖 Agent: {response}")
            # Detect ending phrases in the agent's text
            response_lower = response.lower()
            if any(phrase in response_lower for phrase in ["goodbye", "bye", "have a great day", "ending call"]):
                print("\n👋 Call completion detected. Shutting down...")
                # Give it a small delay so the audio can finish playing
                time.sleep(2) 
                session_active['active'] = False

        conversation = Conversation(
            client=client,
            agent_id=AGENT_ID,
            requires_auth=True,
            audio_interface=audio_interface,
            client_tools=client_tools,
            callback_user_transcript=lambda t: print(f"\n👤 User: {t}"),
            callback_agent_response=handle_agent_response, # Use our new handler
        )

        def safe_end_session():
            if session_active['active']:
                session_active['active'] = False
                try:
                    conversation.end_session()
                except:
                    pass

        def signal_handler(sig, frame):
            safe_end_session()
            print("\n\n✅ Session ended. Goodbye!")
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)

        print("\n" + "="*60)
        print("🍕 MARIO'S PIZZA - CUSTOMER SERVICE")
        print("="*60)
        print("📞 Listening... Speak clearly into your microphone")
        print("🛑 Say 'Cut the call' or press Ctrl+C to end")
        print("="*60 + "\n")
        
        try:
            session_active['active'] = True
            conversation.start_session()
            
            print("✅ Connected! The agent will greet you shortly...\n")
            
            # Keep running until session_active becomes False
            while session_active['active']:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            pass
        except Exception as e:
            error_msg = str(e).lower()
            # Only show unexpected errors
            if "1008" not in error_msg and "policy" not in error_msg:
                print(f"\n⚠️  Session ended: {e}")
        finally:
            safe_end_session()

    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify API_KEY and AGENT_ID are correct")
        print("3. Ensure your microphone is working")

if __name__ == "__main__":
    # Suppress stderr for ALSA warnings
    if sys.stderr.isatty():
        sys.stderr = open(os.devnull, 'w')
    
    main()
