import json
import os
import datetime
import telebot
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
import shutil
STATE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'nutricloud_state.json')
HOME_STATE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'nutricloud_state_home.json')

def get_nutricloud_state() -> str:
    """Reads the current state of NutriCloud including profile (goals, macros, diet), inventory, and historical daily logs. Returns JSON string."""
    if not os.path.exists(STATE_FILE):
        return json.dumps({"error": "State file not found. Assume empty state.", "profile": {}, "inventory": [], "logs": []})
    
    with open(STATE_FILE, 'r') as f:
        return f.read()

def update_nutricloud_state(new_state_json_str: str) -> str:
    """Overwrites the NutriCloud state with the provided JSON string. Use this to update inventory after shopping or logging meals.
    Ensure you preserve all other existing keys in the state when making updates.
    """
    try:
        data = json.loads(new_state_json_str)
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return "Successfully updated NutriCloud state."
    except Exception as e:
        return f"Error updating state: {str(e)}"

def recalculate_profile_targets() -> str:
    """Recalculates the user's BMR, TDEE, Calories, and Macronutrient targets based on their profile data (weight, height, age, gender, leanMass, activity, objective) and saves the updated state. Call this whenever the user asks to update their profile or recalculate targets.
    """
    try:
        if not os.path.exists(STATE_FILE):
            return "Error: State file not found."
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            
        profile = state.get('profile', {})
        if not profile:
            return "Error: Profile is empty, cannot recalculate."
            
        weight = float(profile.get('weight', 0))
        height = float(profile.get('height', 0))
        age = int(profile.get('age', 0))
        gender = profile.get('gender', 'male').lower()
        lean_mass = float(profile.get('leanMass', 0))
        activity = profile.get('activity', 'sedentary').lower()
        objective = profile.get('objective', 'maintain').lower()
        
        # 1. BMR Calculation
        if lean_mass > 0:
            bmr = 370 + (21.6 * lean_mass)
        else:
            if gender == 'female':
                bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
            else:
                bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
                
        # 2. TDEE Calculation
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'extreme': 1.9
        }
        multiplier = 1.2
        for key, val in activity_multipliers.items():
            if key in activity:
                multiplier = val
                break
        tdee = bmr * multiplier
        
        # 3. Target Calories based on objective
        if objective == 'deficit':
            target_calories = tdee * 0.8
        elif objective == 'surplus':
            target_calories = tdee * 1.1
        else:
            target_calories = tdee
            
        # 4. Macronutrients
        if objective == 'deficit':
            protein = (2.2 * lean_mass) if lean_mass > 0 else (1.8 * weight)
        elif objective == 'surplus':
            protein = (1.6 * lean_mass) if lean_mass > 0 else (1.6 * weight)
        else:
            protein = (1.8 * lean_mass) if lean_mass > 0 else (1.6 * weight)
            
        fats = (1.0 * lean_mass) if lean_mass > 0 else (0.65 * weight)
        
        protein_cals = protein * 4
        fats_cals = fats * 9
        carbs_cals = target_calories - protein_cals - fats_cals
        carbs = carbs_cals / 4 if carbs_cals > 0 else 0
        
        profile['bmr'] = round(bmr)
        profile['tdee'] = round(tdee)
        profile['targetCalories'] = round(target_calories)
        profile['targetProtein'] = round(protein)
        profile['targetFat'] = round(fats)
        profile['targetCarbs'] = round(carbs)
        
        state['profile'] = profile
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
            
        return f"Successfully recalculated and updated profile. New Targets -> Calories: {round(target_calories)}, Protein: {round(protein)}g, Fats: {round(fats)}g, Carbs: {round(carbs)}g."
    except Exception as e:
        return f"Error recalculating profile: {str(e)}"

def stash_pantry_for_travel() -> str:
    """Saves the current state as the 'home' state and clears the current pantry inventory for travelling."""
    try:
        if not os.path.exists(STATE_FILE):
            return "Error: Current state file not found."
            
        shutil.copy(STATE_FILE, HOME_STATE_FILE)
        
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            
        # Clear inventory and shopping list for travel
        state['inventory'] = []
        state['shoppingList'] = []
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
            
        return "Pantry successfully stashed for travel! Inventory and shopping list have been cleared. When you return, just ask me to restore the home pantry."
    except Exception as e:
        return f"Error stashing pantry: {str(e)}"

def restore_home_pantry() -> str:
    """Restores the 'home' state pantry that was previously stashed, overwriting the travel inventory but keeping the latest logs and profile."""
    try:
        if not os.path.exists(HOME_STATE_FILE):
            return "Error: No home state found to restore from."
            
        with open(STATE_FILE, 'r') as f:
            current_state = json.load(f)
            
        with open(HOME_STATE_FILE, 'r') as f:
            home_state = json.load(f)
            
        # We only restore the inventory and shopping list from home. We keep the new profile and logs made while traveling!
        current_state['inventory'] = home_state.get('inventory', [])
        current_state['shoppingList'] = home_state.get('shoppingList', [])
        
        with open(STATE_FILE, 'w') as f:
            json.dump(current_state, f, indent=2)
            
        return "Home pantry and shopping list successfully restored! Welcome back."
    except Exception as e:
        return f"Error restoring home pantry: {str(e)}"

def get_current_date() -> str:
    """Returns the current date in YYYY-MM-DD format."""
    return datetime.date.today().strftime("%Y-%m-%d")

# Comprehensive Agent Instruction
NUTRICLOUD_INSTRUCTION = """You are the NutriCloud Manager, an advanced dietary assistant.
You have direct access to the user's NutriCloud state which includes:
- profile: Dietary restrictions (e.g. keto, vegan), objectives (e.g. deficit, surplus), and exact caloric & macronutrient targets.
- inventory: Current food items available in the user's pantry/fridge.
- logs: Historical daily macronutrient logs of what the user has eaten.
- shoppingList: An array of items that the user needs to buy.

ALWAYS follow these rules:
1. STATE AWARENESS: Always use get_nutricloud_state() when the user asks for a meal plan, a shopping list, or updates.
2. MEAL SUGGESTIONS: 
   - Check the `logs` for the current day (use get_current_date() to find out what day today is). 
   - If it's breakfast, plan freely based on inventory and daily targets.
   - If it's lunch or dinner, strictly analyze what has already been eaten today to AVOID repetition (e.g., do not suggest eggs if they already ate eggs for breakfast).
   - Ensure suggestions help the user hit their exact remaining macros for the day, respecting their dietary restrictions.
   - If missing ingredients, warn the user or suggest alternatives.
3. INGREDIENT SUBSTITUTIONS: If asked for alternative ingredients, provide nutritionally adequate substitutes that strictly adhere to their stated dietary restrictions and goals.
4. SHOPPING LISTS & PERSISTENCE: 
   - When generating shopping lists or discussing items the user should buy (either because they are low on stock, or planning for upcoming meals), use `update_nutricloud_state` to explicitly add these items to the `shoppingList` array in the JSON state.
   - When the user confirms they have bought items, remove them from the `shoppingList` and add them to the `inventory`.
5. UPDATING STATE: When the user confirms they have eaten a meal, or confirms they have finished shopping, use update_nutricloud_state() to actively deduct items from the inventory, add items to the inventory, and append the meal to the daily logs. 
   CRITICAL FOR LOGS: Use get_current_date() to determine the current date. The `logs` array must be a flat array of objects. NEVER nest meals inside dates. Every time you log a new meal, you MUST push a new object with the EXACT following keys: `date` (YYYY-MM-DD), `meal` (Breakfast/Lunch/Dinner/Snack), `calories` (integer), `protein` (integer), `carbs` (integer), `fat` (integer), and `items` (a single string with comma-separated items). Always maintain the full structure of the JSON (profile, inventory, logs, shoppingList) when updating.
6. PROFILE RECALCULATION: When the user wants to update their profile stats or recalculate their macro targets, use recalculate_profile_targets() to automatically apply the proper physiological formulas (Mifflin-St. Jeor, Katch-McArdle) and update the state directly.
7. IMAGE PROCESSING & CONFIRMATION:
   - If the user sends an image, determine if it is a grocery haul/receipt OR a cooked meal.
   - For GROCERIES/RECEIPTS: Extract all items, aggregate them by type, and check if they exist in the `inventory` (even if a different brand). DO NOT UPDATE STATE YET. Instead, reply with a single summarized list of the detected items and explicitly ask the user for confirmation (e.g. "Please confirm these additions to your pantry...").
   - For COOKED MEALS: Estimate the quantities, ingredients, and macros (calories, protein, carbs, fat). DO NOT UPDATE STATE YET. Reply with a single summarized list of the estimated ingredients/macros and explicitly ask for confirmation to add to the log and subtract from the pantry.
    - ONLY when the user explicitly confirms (e.g., replies "yes" or modifies the list), use `update_nutricloud_state` to perform the corresponding action.
8. FORMATTING: Use Telegram's HTML syntax for all formatting (<b>bold</b>, <i>italic</i>, <u>underline</u>, <s>strikethrough</s>, <code>inline code</code>, <pre>code block</pre>, <a href="URL">inline URL</a>). NEVER use Markdown asterisks or hashes. NEVER use unsupported HTML tags like <ul>, <ol>, <li>, <p>, <br>, or headers like <h1>. For lists, just use plain text with a dash and a newline (e.g., "- Item 1\n- Item 2").
9. CONCISENESS & TONE: Be direct and concise. Do NOT ask conversational follow-up questions to keep the conversation going. Never end your messages with questions like "Do you need anything else?", "Shall we proceed?", or "Is there anything else I can adjust?". Just confirm the action and stop.
10. TRAVEL MODE: If the user indicates they are traveling, use stash_pantry_for_travel() to backup their home inventory and start a fresh one. When they return, use restore_home_pantry() to bring back their home inventory without losing their travel meal logs.
"""

root_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='nutricloud_manager',
    description='A specialized dietary assistant that manages the NutriCloud state, suggests meals, generates shopping lists, and updates inventory.',
    instruction=NUTRICLOUD_INSTRUCTION,
    tools=[get_nutricloud_state, update_nutricloud_state, recalculate_profile_targets, get_current_date, stash_pantry_for_travel, restore_home_pantry]
)

if __name__ == '__main__':
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_telegram_bot_token_here")
    USER_ID_STR = os.getenv("TELEGRAM_USER_ID", "your_telegram_user_id_here")
    
    if TOKEN == "your_telegram_bot_token_here" or not TOKEN:
        print("Please configure your TELEGRAM_BOT_TOKEN in .env")
        exit(1)
        
    bot = telebot.TeleBot(TOKEN)
    
    try:
        ALLOWED_USER_ID = int(USER_ID_STR)
    except ValueError:
        ALLOWED_USER_ID = None

    @bot.message_handler(commands=['start', 'help'])
    def send_welcome(message):
        if ALLOWED_USER_ID and message.from_user.id != ALLOWED_USER_ID:
            print(f"Ignored message from unauthorized user: {message.from_user.id}")
            return
            
        bot.reply_to(message, "Hello! I am your NutriCloud Manager. How can I help you today?")
        if not ALLOWED_USER_ID:
            bot.reply_to(message, f"Your Telegram User ID is {message.from_user.id}. Please add this to your .env file as TELEGRAM_USER_ID to restrict access to only you.")

    # Instantiate the runner globally so session memory is preserved across messages
    runner = InMemoryRunner(agent=root_agent)
    runner.auto_create_session = True

    @bot.message_handler(content_types=['text', 'photo'])
    def handle_message(message):
        if ALLOWED_USER_ID and message.from_user.id != ALLOWED_USER_ID:
            print(f"Ignored message from unauthorized user: {message.from_user.id}")
            return
            
        print(f"Received message from {message.from_user.id}")
        bot.send_chat_action(message.chat.id, 'typing')
        try:
            parts = []
            if message.photo:
                file_info = bot.get_file(message.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                parts.append(types.Part.from_bytes(data=downloaded_file, mime_type='image/jpeg'))
                
            text_content = message.text or message.caption
            if text_content:
                parts.append(types.Part.from_text(text=text_content))
            elif message.photo:
                parts.append(types.Part.from_text(text="Analyze this image based on my instructions."))
                
            if not parts:
                return

            msg = types.Content(role='user', parts=parts)
            
            response_text = ""
            for event in runner.run(
                user_id=str(message.from_user.id),
                session_id=str(message.from_user.id),
                new_message=msg
            ):
                if getattr(event, 'content', None) and getattr(event.content, 'parts', None):
                    for p in event.content.parts:
                        if getattr(p, 'text', None):
                            response_text += p.text
            
            if not response_text:
                response_text = "I processed your request, but there is no output."
                
            bot.reply_to(message, response_text, parse_mode='HTML')
        except Exception as e:
            bot.reply_to(message, f"An error ccurred: {str(e)}")

    print("Starting NutriCloud Telegram Bot...")
    import time
    import logging
    while True:
        try:
            # logger_level=logging.CRITICAL prevents the huge tracebacks from printing when a timeout happens
            bot.infinity_polling(logger_level=logging.CRITICAL)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)
