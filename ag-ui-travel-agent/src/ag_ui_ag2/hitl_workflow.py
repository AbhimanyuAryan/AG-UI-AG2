import os
import asyncio
import threading
from typing import Annotated, Any, Optional, Dict
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows us to access configuration like API keys securely
load_dotenv()

# Import AutoGen components for agent creation and interaction
from autogen import ConversableAgent, LLMConfig, register_function

# FastAPI for creating the web server
from fastapi import FastAPI

# Fastagency for UI interactions and workflow management
from fastagency import UI
from src.ag_ui_ag2.ag_ui_adapter import AGUIAdapter
from fastagency.runtimes.ag2 import Workflow

# Local project imports for database access and message templates
from src.ag_ui_ag2.database import MEMBER_DATABASE
from src.ag_ui_ag2.messages import SYSTEM_MESSAGE, INITIAL_MESSAGE

# Thread-local storage for tracking thread IDs
# This helps manage state across different conversation threads
thread_local = threading.local()

# Travel agent function to look up member information
def lookup_member(
    member_id: Annotated[str, "User's membership ID"]
) -> dict[str, Any]:
    """Look up member details from the database
    
    This function simulates a database lookup for member information based on their ID.
    It returns member details including name, membership type, and preferences if found.
    
    Args:
        member_id: A string representing the user's membership ID (e.g., P12345)
        
    Returns:
        A dictionary containing member information if found, or error message if not found
    """
    if member_id in MEMBER_DATABASE:
        return {
            "found": True,
            "name": MEMBER_DATABASE[member_id]["name"],
            "membership": MEMBER_DATABASE[member_id]["membership"],
            "preferences": MEMBER_DATABASE[member_id]["preferences"]
        }
    else:
        return {
            "found": False,
            "message": "Member ID not found in our system"
        }

# Function to create personalized itinerary
def create_itinerary(
    destination: Annotated[str, "Travel destination (e.g., New York, Paris, Tokyo)"],
    days: Annotated[int, "Number of days for the trip"],
    membership_type: Annotated[str, "Type of membership (premium or standard)"],
    preferences: Annotated[list, "Traveler preferences (e.g., fine dining, cultural tours)"]
) -> dict[str, Any]:
    """Create a realistic, personalized travel itinerary based on member details.
    
    This function generates a custom travel itinerary for the specified number of days
    at the given destination. The content of the itinerary is tailored based on
    the membership type (premium vs standard) and the user's preferences.
    
    Args:
        destination: City or location where the trip will take place
        days: Number of days the itinerary should cover
        membership_type: The user's membership level (premium or standard)
        preferences: List of strings representing user's travel preferences
        
    Returns:
        A dictionary containing the complete itinerary with daily activities,
        accommodation and transportation details
    """
    
    if not destination or days <= 0:
        return {"error": "Invalid destination or number of days."}

    itinerary = []
    for day in range(1, days + 1):
        day_plan = {
            "day": f"Day {day}",
            "morning": "",
            "afternoon": "",
            "evening": "",
        }

        # Differentiate activities based on membership type
        if membership_type == "premium":
            day_plan["morning"] = f"Private tour or exclusive experience aligned with: {', '.join(preferences)}"
            day_plan["afternoon"] = "Relax at a luxury spa, explore high-end shopping districts, or enjoy curated local experiences."
            day_plan["evening"] = "Dine at a top-rated restaurant with a reservation made just for you."
        else:
            day_plan["morning"] = f"Join a small group tour covering key attractions related to: {', '.join(preferences)}"
            day_plan["afternoon"] = "Take a self-guided walk or visit a popular local spot recommended by travel experts."
            day_plan["evening"] = "Enjoy a casual dinner at a popular neighborhood restaurant."

        itinerary.append(day_plan)

    return {
        "destination": destination,
        "days": days,
        "itinerary": itinerary,
        "accommodation": "5-star hotel" if membership_type == "premium" else "3-star or boutique hotel",
        "transportation": "Private car service" if membership_type == "premium" else "Local transport and shared rides",
        "is_draft": True
    }

# Configure LLM
llm_config = LLMConfig(
    model="gpt-4o-mini",  # Specify which OpenAI model to use
    api_key=os.getenv("OPENAI_API_KEY"),  # Get API key from environment variables
)

# Initialize the workflow manager
wf = Workflow()

@wf.register(name="hitl_workflow", description="A simple travel itenarary generator workflow")
def hitl_workflow(ui: UI, params: dict[str, Any]) -> str:
    """Main workflow function that orchestrates the travel planning conversation
    
    This function:
    1. Initializes the conversation with a welcome message
    2. Creates the AI travel agent with system instructions
    3. Creates a customer agent that proxies for human input
    4. Registers tool functions that the travel agent can call
    5. Starts the conversation between agents
    6. Processes and returns the conversation results
    
    Args:
        ui: User interface object for handling user interactions
        params: Additional parameters passed to the workflow
        
    Returns:
        Processed conversation results as string
    """
    # Display initial welcome message to the user
    initial_message = ui.text_input(
        sender="Workflow",
        recipient="User",
        prompt=INITIAL_MESSAGE,
    )
    
    # Create the travel agent with LLM capabilities
    with llm_config:
        travel_agent = ConversableAgent(
                name="travel_agent",
                system_message=SYSTEM_MESSAGE  # Set the agent's behavior and knowledge
            )
        

    # Create the customer agent to represent the human user
    customer = ConversableAgent(
        name="customer",
        human_input_mode="ALWAYS",  # Always ask for human input on this agent's turn
    )

    # Register the functions for the travel agent
    register_function(
        lookup_member,
        caller=travel_agent,  # The agent that can call this function
        executor=customer,    # The agent that will execute the function (human in this case)
        description="Look up member details from the database"
    )

    register_function(
        create_itinerary,
        caller=travel_agent,  # The agent that can call this function
        executor=customer,    # The agent that will execute the function (human in this case)
        description="Create a personalized travel itinerary based on member details"
    )

    # Start the conversation between the travel agent and customer
    response = customer.run(
        travel_agent,               # The agent to converse with
        message=initial_message,    # Initial message to start the conversation
        summary_method="reflection_with_llm"  # Method to summarize the conversation
    )

    # Process and return the conversation results
    return ui.process(response)  # type: ignore[no-any-return]


def without_customer_messages(message: Any) -> bool:
    """Filter function to exclude customer messages from the response
    
    This ensures that only travel agent messages are sent to the frontend,
    filtering out any messages from the customer agent.
    
    Args:
        message: The message to filter
        
    Returns:
        Boolean indicating whether the message should be included (True) or filtered out (False)
    """
    return not (message.type == "text" and message.content.sender == "customer")


# Create an adapter that connects our workflow to the AG-UI protocol
adapter = AGUIAdapter(
    provider=wf,                          # The workflow provider
    wf_name="hitl_workflow",              # The name of the workflow to expose
    filter=without_customer_messages      # Filter to apply to messages
)

# Create FastAPI application and include the adapter's router
app = FastAPI()
app.include_router(adapter.router)        # This adds all required endpoints
