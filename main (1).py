import os
import json
import secrets
import sys
import warnings
from elevenlabs.client import ElevenLabs
from elevenlabs.conversational_ai.conversation import Conversation, ClientTools
from elevenlabs.conversational_ai.default_audio_interface import DefaultAudioInterface

# Suppress warnings
warnings.filterwarnings("ignore")
os.environ['LIBASOUND_THREAD_SAFE'] = '0'

# --- CONFIGURATION ---
# Replace with your actual credentials
AGENT_ID = "agent_8101kd5d5c3ffpbb9sqrzrm9htsy"
API_KEY = "sk_66f0aea5b12ee6c4587e00c381cb0d11be7ca5f1e8d91ee5"

# --- 1. SETUP TOOLS ---
client_tools = ClientTools()

def get_order_status(params):
    """Get order status - returns ONLY the raw data as a JSON string."""
    print("\n🚀 [TOOL CALLED] get_order_status was triggered!") 
    
    # Ensure params is a dict (ElevenLabs sometimes passes a string if using old models)
    if isinstance(params, str):
        params = json.loads(params)

    order_id = str(params.get("order_id", "")).strip()
    print(f"📊 Looking for Order ID: '{order_id}'")
    
    if not order_id:
        return json.dumps({"error": "no_order_id"})
    
    try:
        # Create default file if missing
        if not os.path.exists("orders.json"):
            default_orders = {"1": "Delivered", "2": "Out for delivery", "3": "Delayed"}
            with open("orders.json", "w") as f:
                json.dump(default_orders, f)
        
        with open("orders.json", "r") as file:
            orders = json.load(file)

        status = orders.get(order_id)

        if status:
            print(f"   ✅ Found: {status}")
            result = {
                "order_id": order_id,
                "status": status
            }
            # CRITICAL FIX: Must return a JSON string, not a dict
            return json.dumps(result)
        else:
            print(f"   ❌ Not found")
            return json.dumps({"order_id": order_id, "error": "order_not_found"})
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return json.dumps({"error": "system_error"})

def generate_discount(params):
    """Generate discount code - returns ONLY the code."""
    code_suffix = secrets.token_hex(3).upper()
    new_code = f"PIZZA5-{code_suffix}"
    
    print(f"\n💰 [Tool] Generated: {new_code}")
    
    result = {
        "discount_code": new_code,
        "discount_amount": "$5"
    }
    # CRITICAL FIX: Must return a JSON string
    return json.dumps(result)

# Register tools
client_tools.register("get_order_status", get_order_status)
client_tools.register("generate_discount", generate_discount)

# --- 2. MAIN CONVERSATION LOOP ---
def main():
    if not API_KEY or "YOUR_ACTUAL_API" in API_KEY:
        print("❌ ERROR: Please set your API_KEY and AGENT_ID.")
        return

    print("🔧 Initializing Pizza Agent...")
    
    try:
        client = ElevenLabs(api_key=API_KEY)
        audio_interface = DefaultAudioInterface()

        conversation = Conversation(
            client=client,
            agent_id=AGENT_ID,
            requires_auth=True,
            audio_interface=audio_interface,
            client_tools=client_tools,
            callback_user_transcript=lambda t: print(f"\n👤 User: {t}"),
            callback_agent_response=lambda r: print(f"🤖 Agent: {r}"),
        )
        
        print("\n" + "="*60)
        print("🍕 MARIO'S PIZZA - CUSTOMER SERVICE")
        print("="*60)
        
        conversation.start_session()
        
        # Keep alive
        signal_event = helpers_get_signal()
        signal_event.wait()
            
        conversation.end_session()

    except Exception as e:
        print(f"❌ Session Error: {e}")

def helpers_get_signal():
    import threading
    event = threading.Event()
    return event

if __name__ == "__main__":
    if sys.stderr.isatty():
        sys.stderr = open(os.devnull, 'w')
    main()
