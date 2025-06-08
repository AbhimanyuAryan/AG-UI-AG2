import os
import asyncio
from typing import Annotated, Any, Optional, Dict
from uuid import uuid4
from dotenv import load_dotenv
import logging

# Configure detailed logging for this module
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Use the newer autogen API that's compatible with your installation
try:
    from autogen import ConversableAgent, register_function, ChatResult
    logger.info("Successfully imported AutoGen components")
except ImportError as e:
    logger.error(f"Failed to import AutoGen: {e}")
    raise

MEMBER_DATABASE = {
    "P12345": {
        "name": "Alex Johnson",
        "membership": "premium",
        "preferences": [
            "5-star hotels",
            "fine dining",
            "private tours",
            "exclusive experiences",
        ],
    },
    "P67890": {
        "name": "Taylor Williams",
        "membership": "premium",
        "preferences": [
            "boutique hotels",
            "local cuisine",
            "cultural experiences",
            "adventure activities",
        ],
    },
    "S12345": {
        "name": "Jordan Smith",
        "membership": "standard",
        "preferences": ["budget-friendly", "popular attractions"],
    },
    "S67890": {
        "name": "Casey Brown",
        "membership": "standard",
        "preferences": ["family-friendly", "group tours"],
    },
}

SYSTEM_MESSAGE = """You are a professional travel agent who creates detailed, personalized day-by-day travel itineraries for any destination.

WORKFLOW:
1. Greet the customer warmly and ask for their member ID.
2. Use the `lookup_member` function to retrieve their profile information.
3. Address the customer by name and acknowledge their membership level (premium or standard).
4. Ask for their desired destination, specific cities (if applicable), travel start date, and trip duration.
5. Use the `create_itinerary` function to generate a personalized day-by-day itinerary.
6. Present the itinerary with clear headers and formatting.
7. Ask if the customer would like to modify any days or experiences.
8. Once finalized, confirm the itinerary and thank them for using the service.

Tone: Friendly, professional, and knowledgeable.
"""

INITIAL_MESSAGE = """Hi there! 👋 I'm your personal Travel Guide, here to help you plan an unforgettable trip.

To get started, could you please share your membership ID? This will help me tailor recommendations based on your preferences and travel style.

(Hint: You can try using one of these IDs: P12345, P67890, S12345, S67890. When I ask for permission to execute functions, please say "continue" to proceed.)
"""

def lookup_member(member_id: Annotated[str, "User's membership ID"]) -> dict[str, Any]:
    """Look up member details from the database"""
    logger.info(f"[TOOL] lookup_member called with ID: {member_id}")
    
    if member_id in MEMBER_DATABASE:
        result = {
            "found": True,
            "name": MEMBER_DATABASE[member_id]["name"],
            "membership": MEMBER_DATABASE[member_id]["membership"],
            "preferences": MEMBER_DATABASE[member_id]["preferences"]
        }
        logger.info(f"[TOOL] Member found: {result}")
        return result
    else:
        result = {
            "found": False,
            "message": "Member ID not found in our system"
        }
        logger.warning(f"[TOOL] Member not found: {member_id}")
        return result

def create_itinerary(
    destination: Annotated[str, "Travel destination"],
    days: Annotated[int, "Number of days for the trip"],
    membership_type: Annotated[str, "Type of membership (premium or standard)"],
    preferences: Annotated[list, "Traveler preferences"]
) -> dict[str, Any]:
    """Create a realistic, personalized travel itinerary"""
    logger.info(f"[TOOL] create_itinerary called:")
    logger.info(f"[TOOL]   destination: {destination}")
    logger.info(f"[TOOL]   days: {days}")
    logger.info(f"[TOOL]   membership_type: {membership_type}")
    logger.info(f"[TOOL]   preferences: {preferences}")
    
    if not destination or days <= 0:
        error_result = {"error": "Invalid destination or number of days."}
        logger.error(f"[TOOL] Invalid parameters: {error_result}")
        return error_result

    itinerary = []
    for day in range(1, days + 1):
        logger.debug(f"[TOOL] Creating day {day} plan")
        day_plan = {
            "day": f"Day {day}",
            "morning": "",
            "afternoon": "",
            "evening": "",
        }

        if membership_type == "premium":
            day_plan["morning"] = f"Private tour or exclusive experience aligned with: {', '.join(preferences)}"
            day_plan["afternoon"] = "Relax at a luxury spa, explore high-end shopping districts, or enjoy curated local experiences."
            day_plan["evening"] = "Dine at a top-rated restaurant with a reservation made just for you."
        else:
            day_plan["morning"] = f"Join a small group tour covering key attractions related to: {', '.join(preferences)}"
            day_plan["afternoon"] = "Take a self-guided walk or visit a popular local spot recommended by travel experts."
            day_plan["evening"] = "Enjoy a casual dinner at a popular neighborhood restaurant."

        itinerary.append(day_plan)

    result = {
        "destination": destination,
        "days": days,
        "itinerary": itinerary,
        "accommodation": "5-star hotel" if membership_type == "premium" else "3-star or boutique hotel",
        "transportation": "Private car service" if membership_type == "premium" else "Local transport and shared rides",
        "is_draft": True
    }
    
    logger.info(f"[TOOL] Itinerary created successfully for {destination}")
    return result

# Update the LLM config to use the newer format that's compatible with ag2
llm_config = {
    "config_list": [
        {
            "model": "gpt-4o-mini",
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
    ],
    "temperature": 0.7,
    "timeout": 60,
}

def hitl_workflow(initial_user_message: str, ui=None, params: Optional[dict[str, Any]] = None) -> None:
    """Main workflow function that orchestrates the travel planning conversation"""
    if params is None:
        params = {}
    
    logger.info(f"[WORKFLOW] Starting workflow")
    logger.info(f"[WORKFLOW] Initial user message: \"{initial_user_message}\"")
    logger.info(f"[WORKFLOW] UI provided: {ui is not None}")
    logger.info(f"[WORKFLOW] Params: {params}")
    
    try:
        logger.info(f"[WORKFLOW] Creating travel agent...")
        travel_agent = ConversableAgent(
            name="travel_agent",
            system_message=SYSTEM_MESSAGE,
            llm_config=llm_config,
            code_execution_config=False,  # Disable code execution
            human_input_mode="NEVER",  # Agent should never ask for human input directly
            max_consecutive_auto_reply=10,  # Limit auto replies
        )
        logger.info(f"[WORKFLOW] Travel agent created successfully")
        
        # Create a custom UI-aware customer agent
        if ui:
            logger.info(f"[WORKFLOW] Creating UI customer agent...")
            customer = UICustomerAgent(
                name="customer",
                ui=ui,
                llm_config=llm_config,
            )
            logger.info(f"[WORKFLOW] UI customer agent created")
        else:
            logger.info(f"[WORKFLOW] Creating console customer agent...")
            customer = ConversableAgent(
                name="customer",
                human_input_mode="ALWAYS",
                llm_config=llm_config,
                code_execution_config=False,
                default_auto_reply="Please provide input.",
                max_consecutive_auto_reply=1,
            )
            logger.info(f"[WORKFLOW] Console customer agent created")

        # Register functions with updated API
        logger.info(f"[WORKFLOW] Registering lookup_member function...")
        register_function(
            lookup_member,
            caller=travel_agent,
            executor=customer,
            name="lookup_member",
            description="Look up member details from the database using their member_id."
        )
        logger.info(f"[WORKFLOW] lookup_member function registered")

        logger.info(f"[WORKFLOW] Registering create_itinerary function...")
        register_function(
            create_itinerary,
            caller=travel_agent,
            executor=customer,
            name="create_itinerary",
            description="Create a personalized travel itinerary based on member details."
        )
        logger.info(f"[WORKFLOW] create_itinerary function registered")
        
        logger.info(f"[WORKFLOW] Starting conversation between agents...")
        
        # Start the conversation with the updated API
        logger.info(f"[WORKFLOW] Customer initiating chat with travel agent...")
        chat_result: Optional[ChatResult] = customer.initiate_chat(
            travel_agent,
            message=initial_user_message,
            max_turns=20,  # Increase max turns for full conversation
            clear_history=True,  # Start with clean history
            silent=False,  # Enable logging
        )

        logger.info(f"[WORKFLOW] Conversation completed")
        
        if chat_result:
            logger.info(f"[WORKFLOW] Chat result received, processing messages...")
            logger.info(f"[WORKFLOW] Chat history length: {len(chat_result.chat_history) if chat_result.chat_history else 0}")
            
            # Log the full chat history for debugging
            if chat_result.chat_history:
                for i, msg in enumerate(chat_result.chat_history):
                    logger.info(f"[WORKFLOW] Message {i}: {msg}")
            
            if ui:
                # Process final messages through UI
                logger.info(f"[WORKFLOW] Processing final messages through UI...")
                logger.info(f"[WORKFLOW] Workflow completed successfully")
        else:
            logger.warning(f"[WORKFLOW] No chat result received")
            
    except Exception as e:
        logger.error(f"[WORKFLOW] Error in workflow execution: {e}", exc_info=True)
        # Don't re-raise the exception, just log it
        if ui:
            # Try to send an error message through UI
            try:
                # Use a simpler error handling approach
                logger.info(f"[WORKFLOW] Attempting to send error through UI...")
                # Don't try to create event loops here, just log the error
                logger.error(f"[WORKFLOW] Error details: {str(e)}")
            except Exception as ui_error:
                logger.error(f"[WORKFLOW] Error sending error message through UI: {ui_error}")

class UICustomerAgent(ConversableAgent):
    """Custom agent that integrates with our FastAPI UI"""
    
    def __init__(self, name: str, ui, **kwargs):
        logger.info(f"[AGENT] Creating UICustomerAgent: {name}")
        # Remove any problematic config and set safe defaults
        safe_kwargs = {k: v for k, v in kwargs.items() if k not in ['proxies']}
        super().__init__(
            name=name, 
            human_input_mode="ALWAYS", 
            code_execution_config=False,
            max_consecutive_auto_reply=1,
            **safe_kwargs
        )
        self.ui = ui
        logger.info(f"[AGENT] UICustomerAgent created: {name}")
    
    def get_human_input(self, prompt: str) -> str:
        """Override to get input through UI instead of console"""
        logger.info(f"[AGENT] get_human_input called")
        logger.info(f"[AGENT] Prompt: {prompt}")
        
        if self.ui:
            logger.info(f"[AGENT] Using UI for input")
            try:
                logger.info(f"[AGENT] Calling UI text_input synchronously...")
                
                # Use a simpler approach - create a new event loop each time
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    response = loop.run_until_complete(
                        self.ui.text_input("travel_agent", "customer", prompt)
                    )
                    logger.info(f"[AGENT] Received response from UI: {response}")
                    return response
                finally:
                    loop.close()
                    
            except Exception as e:
                logger.error(f"[AGENT] Error getting input through UI: {e}", exc_info=True)
                return "continue"  # Default response on error
        else:
            logger.info(f"[AGENT] Using console for input")
            response = input(prompt)
            logger.info(f"[AGENT] Console response: {response}")
            return response

if __name__ == "__main__":
    print("Travel Agent Console Application")
    print("--------------------------------")
    print(INITIAL_MESSAGE)
    
    user_input = ""
    while not user_input.strip():
        user_input = input("> ")
        if not user_input.strip():
            print("Please provide an initial request, or type 'exit' to quit.")
        if user_input.strip().lower() == 'exit':
            print("Exiting application.")
            exit()
            
    hitl_workflow(initial_user_message=user_input)
    print("\nApplication finished.")