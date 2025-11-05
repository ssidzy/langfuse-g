from dotenv import load_dotenv
from langfuse import Langfuse, get_client

import os
load_dotenv()

#----------------------
#Client Initialization
#----------------------

# Option 1: Initialize from environment variables (recommended)
#langfuse = Langfuse()

# Option 2: Explicit initialization
langfuse = Langfuse(
    public_key=os.environ.get('LANGFUSE_PUBLIC_KEY'),
    secret_key=os.environ.get('LANGFUSE_SECRET_KEY'),
    base_url=os.environ.get('LANGFUSE_BASE_URL')
)

# Option 3: Get global singleton client
#langfuse = get_client()

# Verify connection (not recommended in production due to added latency)
if langfuse.auth_check():
    print("Connected to Langfuse!")


#-----------------------------
#Creating and Managing Prompts
#-----------------------------

# Helper function to check if prompt exists
def prompt_exists(name, label=None):
    try:
        langfuse.get_prompt(name, label=label if label else "production")
        return True
    except:
        return False

#Text Prompts (single-turn):
if not prompt_exists("text-analyzer"):
    langfuse.create_prompt(
        name="text-analyzer",
        type="text",
        prompt="Analyze the following text and provide {{analysis_type}} insights: {{text}}",
        labels=["production"],  # Immediately available in production
        config={
            "model": "gpt-4o",
            "temperature": 0.7,
            "max_tokens": 1000,
            "description": "Text analysis prompt for various use cases"
        }
    )
    print("Created prompt: text-analyzer")
else:
    print("Prompt 'text-analyzer' already exists, skipping creation")

#Chat Prompts (multi-turn conversations):
if not prompt_exists("code-reviewer"):
    langfuse.create_prompt(
        name="code-reviewer",
        type="chat",
        prompt=[
            {
                "role": "system",
                "content": "You are an expert {{language}} code reviewer. Focus on {{focus_areas}}."
            },
            {
                "role": "user",
                "content": "Review this code:\n\n{{code}}"
            }
        ],
        labels=["production"],
        config={
            "model": "gpt-4o",
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
    )
    print("Created prompt: code-reviewer")
else:
    print("Prompt 'code-reviewer' already exists, skipping creation")


#Function Calling Prompts
if not prompt_exists("data-extractor", label="staging"):
    langfuse.create_prompt(
        name="data-extractor",
        type="chat",
        prompt=[
            {"role": "system", "content": "Extract structured data from the text."},
            {"role": "user", "content": "{{input_text}}"}
        ],
        labels=["staging"],
        config={
            "model": "gpt-4o",
            "temperature": 0,
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "extract_data",
                        "description": "Extract structured data",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"}
                            }
                        }
                    }
                }
            ]
        }
    )
    print("Created prompt: data-extractor")
else:
    print("Prompt 'data-extractor' already exists, skipping creation")



#------------------------------
#Fetching and Compiling Prompts
#------------------------------

#Fetching by Label (most common in production):

# Fetch current production version
prompt = langfuse.get_prompt("text-analyzer")  # Defaults to "production" label
print("Prompt Fetched: ",prompt)

production_prompt = langfuse.get_prompt("text-analyzer", label="production")
print("Production prompt fetched: ",production_prompt)

# Fetch staging version for testing
# staging_prompt = langfuse.get_prompt("text-analyzer", label="staging")  # Not created

# Fetch latest version (always most recent)
# latest_prompt = langfuse.get_prompt("text-analyzer", label="latest")  # Not created


#Fetching by Version Number (for reproducibility):
# Fetch specific version
# prompt_v1 = langfuse.get_prompt("text-analyzer", version=1)  # Not created
# prompt_v2 = langfuse.get_prompt("text-analyzer", version=2)  # Not created



#--------------------------------
#Compiling Prompts with Variables
#--------------------------------

# For text prompts ( input Variables )
compiled_text = prompt.compile(
    analysis_type="sentiment",
    text="This product is amazing!"
)
print("Compiled Text: ", compiled_text)

# Result: "Analyze the following text and provide sentiment insights: This product is amazing!"

# For chat prompts
chat_prompt = langfuse.get_prompt("code-reviewer", type="chat")
print("Chat prompt fetched: ", chat_prompt)
compiled_chat = chat_prompt.compile(
    language="Python",
    focus_areas="performance and security",
    code="def hello(): print('world')"
)
print("Compiled Chat: ", compiled_chat)
# Result: List of chat messages with variables replaced

# Access prompt attributes
raw_template = prompt.prompt  # Original template with {{variables}}
print("Raw template: ", raw_template)
config = prompt.config  # Configuration object
print("Config: ", config)
model = prompt.config.get("model")  # Get specific config value
print("Model: ", model)



#----------------------------------
#Versioning and Deployment Workflow
#----------------------------------

#Version Control and Label Management

#Creating New Versions
# Create initial version
if not prompt_exists("customer-support"):
    langfuse.create_prompt(
        name="customer-support",
        type="chat",
        prompt=[
            {"role": "system", "content": "You are a helpful support agent."},
            {"role": "user", "content": "{{user_query}}"}
        ],
        labels=["production"],
        config={"model": "gpt-3.5-turbo", "temperature": 0.7}
    )
    print("Created prompt: customer-support (version 1)")
    # This creates version 1 with label "production"
    fetch1 = langfuse.get_prompt("customer-support", type="chat")
    print("fetched customer-support in production: ", fetch1.prompt)
else:
    print("Prompt 'customer-support' already exists, skipping creation")
    fetch1 = langfuse.get_prompt("customer-support", type="chat")
    print("fetched customer-support in production: ", fetch1.prompt)

# Create improved version (same name = new version)
if not prompt_exists("customer-support", label="staging"):
    langfuse.create_prompt(
        name="customer-support",  # Same name
        type="chat",
        prompt=[
            {"role": "system", "content": "You are an empathetic support agent. Always be polite."},
            {"role": "user", "content": "{{user_query}}"}
        ],
        labels=["staging"],  # Test in staging first
        config={"model": "gpt-4o", "temperature": 0.5}
    )
    print("Created prompt: customer-support (version 2 - staging)")
    # This creates version 2 with label "staging"
    fetch2 = langfuse.get_prompt("customer-support", type="chat")
    print("fetched customer-support after updating to staging: ", fetch2.prompt)
else:
    print("Prompt 'customer-support' with staging label already exists, skipping creation")
    fetch2 = langfuse.get_prompt("customer-support", type="chat")
    print("fetched customer-support after updating to staging: ", fetch2.prompt)

#Updating Labels Programmatically:
# After testing version 2 in staging, promote to production
langfuse.update_prompt(
    name="customer-support",
    version=4,
    new_labels=["production"]  # Moves production label to version 2
)

# Rollback to previous version
langfuse.update_prompt(
    name="customer-support",
    version=2,
    new_labels=["production"]  # Rollback to version 1
)


prompt_v1 = langfuse.get_prompt("customer-support", version=1)  # Not created
prompt_v2 = langfuse.get_prompt("customer-support", version=2)  # Not created
prompt_v3 = langfuse.get_prompt("customer-support", version=3)  # Not created
prompt_v4 = langfuse.get_prompt("customer-support", version=4)  # Not created

print("Latest: ", langfuse.get_prompt("customer-support"),langfuse.get_prompt("customer-support").version,langfuse.get_prompt("customer-support").prompt)

print("Prompt 1",prompt_v1.prompt)
print("Prompt 2",prompt_v2.prompt)
print("Prompt 1",prompt_v3.prompt)
print("Prompt 2",prompt_v4.prompt)


#-------------------------------------
#Performance Optimization with Caching
#-------------------------------------



