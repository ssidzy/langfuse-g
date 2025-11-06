from dotenv import load_dotenv
from langfuse import Langfuse, get_client, observe

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



#-------------------------------------
#TRACING: Observability and Monitoring
#-------------------------------------

# Tracing tracks your function calls automatically
# You don't need to use prompts - tracing works with ANY function!

# Example 1: Simple traced function (no LLM, just tracking)
@observe()
def process_data(data):
    """This function will be traced - inputs, outputs, execution time logged"""
    result = data.upper()
    return result

# Example 2: Traced function using a prompt
@observe()
def analyze_text_with_prompt(text, analysis_type="sentiment"):
    """Combines prompt management + tracing"""
    # Fetch and compile prompt
    prompt = langfuse.get_prompt("text-analyzer")
    compiled = prompt.compile(analysis_type=analysis_type, text=text)
    
    # Simulate LLM call (replace with actual API call)
    # response = openai.chat.completions.create(...)
    response = f"Analyzed: {compiled}"
    
    return response

# Example 3: Nested tracing (parent-child relationship)
@observe()
def extract_keywords(text):
    """Child function - will be nested under parent trace"""
    keywords = text.split()[:5]
    return keywords

@observe()
def comprehensive_analysis(text):
    """Parent function - creates trace hierarchy"""
    # This call will be nested in the trace
    keywords = extract_keywords(text)
    
    # Another nested call
    sentiment = analyze_text_with_prompt(text, "sentiment")
    
    return {
        "keywords": keywords,
        "sentiment": sentiment
    }

# Example 4: Custom trace attributes and metadata
@observe(name="custom-analyzer")
def custom_traced_function(input_text):
    """You can customize trace name and add metadata"""
    return f"Processed: {input_text}"


# Run the traced functions
print("\n" + "="*50)
print("TESTING TRACING FEATURES")
print("="*50 + "\n")

# Test simple tracing
result1 = process_data("hello world")
print(f"1. Simple trace result: {result1}")

# Test prompt + tracing
result2 = analyze_text_with_prompt("This product is great!", "sentiment")
print(f"2. Prompt + trace result: {result2}")

# Test nested tracing
result3 = comprehensive_analysis("AI ML Python Data Science Technology")
print(f"3. Nested trace result: {result3}")

# Test custom attributes
result4 = custom_traced_function("test input")
print(f"4. Custom trace result: {result4}")

print("\n" + "="*50)
print("All traces sent to Langfuse dashboard!")
print("="*50 + "\n")

# IMPORTANT: Flush traces before script exits
# This ensures all trace data is sent to Langfuse cloud
langfuse.flush()
print("Traces flushed successfully!")

