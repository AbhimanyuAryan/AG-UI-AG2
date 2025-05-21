import os
import asyncio
import threading
from typing import Annotated, Any, Optional, Dict
from uuid import uuid4
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from autogen import ConversableAgent, LLMConfig, register_function

from fastapi import FastAPI

from fastagency import UI
from src.ag_ui_ag2.ag_ui_adapter import AGUIAdapter
from fastagency.runtimes.ag2 import Workflow
from src.ag_ui_ag2.database import MEMBER_DATABASE
from src.ag_ui_ag2.messages import SYSTEM_MESSAGE, INITIAL_MESSAGE

# Thread-local storage for tracking thread IDs
thread_local = threading.local()

# Travel agent function to look up member information
def lookup_member(
    member_id: Annotated[str, "User's membership ID"]
) -> dict[str, Any]:
    """Look up member details from the database"""
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
    """Create a realistic, personalized travel itinerary based on member details."""
    
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
    model="gpt-4o-mini",
    api_key=os.getenv("OPENAI_API_KEY"),
)

wf = Workflow()

@wf.register(name="hitl_workflow", description="A simple travel itenarary generator workflow")
def hitl_workflow(ui: UI, params: dict[str, Any]) -> str:
    initial_message = ui.text_input(
        sender="Workflow",
        recipient="User",
        prompt=INITIAL_MESSAGE,
    )
    
    # Create the travel agent
    with llm_config:
        travel_agent = ConversableAgent(
                name="travel_agent",
                system_message=SYSTEM_MESSAGE
            )
        

    # Create the customer agent (human input)
    customer = ConversableAgent(
        name="customer",
        human_input_mode="ALWAYS",  # Always ask for human input
    )

    # Register the functions for the travel agent
    register_function(
        lookup_member,
        caller=travel_agent,
        executor=customer,
        description="Look up member details from the database"
    )

    register_function(
        create_itinerary,
        caller=travel_agent,
        executor=customer,
        description="Create a personalized travel itinerary based on member details"
    )

    # Start the conversation
    response = customer.run(
        travel_agent,
        message=initial_message,
        summary_method="reflection_with_llm"
    )

    return ui.process(response)  # type: ignore[no-any-return]


def without_customer_messages(message: Any) -> bool:
    return not (message.type == "text" and message.content.sender == "customer")


adapter = AGUIAdapter(
    provider=wf, wf_name="hitl_workflow", filter=without_customer_messages
)

app = FastAPI()
app.include_router(adapter.router)
