import json
import os
from google.adk.agents.llm_agent import Agent

# Define the absolute path to the config folder and state file
STATE_FILE = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'nutricloud_state.json')

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

# Comprehensive Agent Instruction
NUTRICLOUD_INSTRUCTION = """You are the NutriCloud Manager, an advanced dietary assistant.
You have direct access to the user's NutriCloud state which includes:
- profile: Dietary restrictions (e.g. keto, vegan), objectives (e.g. deficit, surplus), and exact caloric & macronutrient targets.
- inventory: Current food items available in the user's pantry/fridge.
- logs: Historical daily macronutrient logs of what the user has eaten.

ALWAYS follow these rules:
1. STATE AWARENESS: Always use get_nutricloud_state() when the user asks for a meal plan, a shopping list, or updates.
2. MEAL SUGGESTIONS: 
   - Check the `logs` for the current day. 
   - If it's breakfast, plan freely based on inventory and daily targets.
   - If it's lunch or dinner, strictly analyze what has already been eaten today to AVOID repetition (e.g., do not suggest eggs if they already ate eggs for breakfast).
   - Ensure suggestions help the user hit their exact remaining macros for the day, respecting their dietary restrictions.
   - If missing ingredients, warn the user or suggest alternatives.
3. INGREDIENT SUBSTITUTIONS: If asked for alternative ingredients, provide nutritionally adequate substitutes that strictly adhere to their stated dietary restrictions and goals.
4. SHOPPING LISTS: Generate shopping lists covering the requested number of days. Calculate the necessary quantities of food needed to hit their exact caloric and nutrient requirements, minus what is currently in the `inventory`.
5. UPDATING STATE: When the user confirms they have eaten a meal, or confirms they have finished shopping, use update_nutricloud_state() to actively deduct items from the inventory, add items to the inventory, and append the meal to the daily logs. Always maintain the full structure of the JSON (profile, inventory, logs) when updating.
6. PROFILE RECALCULATION: When the user wants to update their profile stats or recalculate their macro targets, use recalculate_profile_targets() to automatically apply the proper physiological formulas (Mifflin-St. Jeor, Katch-McArdle) and update the state directly.
"""

root_agent = Agent(
    model='gemini-3.1-flash-lite',
    name='nutricloud_manager',
    description='A specialized dietary assistant that manages the NutriCloud state, suggests meals, generates shopping lists, and updates inventory.',
    instruction=NUTRICLOUD_INSTRUCTION,
    tools=[get_nutricloud_state, update_nutricloud_state, recalculate_profile_targets]
)
