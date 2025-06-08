import os
from dotenv import load_dotenv

load_dotenv()

# Test OpenAI configuration
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY not found in environment")
    exit(1)
else:
    print(f"✅ OPENAI_API_KEY found: {api_key[:10]}...")

# Test AutoGen import
try:
    from autogen import ConversableAgent
    print("✅ AutoGen imported successfully")
except ImportError as e:
    print(f"❌ AutoGen import failed: {e}")
    exit(1)

# Test OpenAI client creation
try:
    llm_config = {
        "config_list": [
            {
                "model": "gpt-4o-mini",
                "api_key": api_key,
            }
        ],
        "temperature": 0.7,
    }
    
    agent = ConversableAgent(
        name="test_agent",
        system_message="You are a test agent.",
        llm_config=llm_config,
        code_execution_config=False,
    )
    print("✅ ConversableAgent created successfully")
    
except Exception as e:
    print(f"❌ Agent creation failed: {e}")
    exit(1)

print("🎉 All tests passed! Configuration is working.")
