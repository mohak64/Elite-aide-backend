import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Replace with your OpenAI API key (remove from code for deployment)
os.environ["OPENAI_API_KEY"] = "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"

# Define task structure
class Task:
    def __init__(self, type: str, title: str, description: str, priority: str, completion_date: str):
        self.type = type
        self.title = title
        self.description = description
        self.priority = priority
        self.completion_date = completion_date

def create_prompt_template():
    """
    Defines the prompt template for LangChain LLM
    """
    return PromptTemplate(
        input_variables=["input"],
        template="""
        You are a highly advanced and accurate AI assistant for a comprehensive task management mobile application, similar to advanced AI systems like EMA or FloodHQ. Your role is to extract and process information from the user's input string, focusing on various types of tasks including household, work/professional, personal, errands, family and social, health and wellness, financial, educational/skill development, travel and leisure, and miscellaneous tasks.

Extract the following information from the user's input:

- Type: The category of the task (e.g., Household, Work/Professional, Personal, etc.)
- Title: A brief, clear title for the task
- Description: A detailed description of the task
- Priority: Low, medium, or high
- Completion Date: The date and time when the task needs to be completed

User Input: {input}

Please provide the extracted information in the following format:

Autocomplete: {autocomplete}
Type: {type}
Title: {title}
Description: {desc}
Priority: {priority}
Completion Date: {completion_date}

Protocols you MUST follow:
1. Dates and Calendar:
   - Always use the most up-to-date calendar for the year 2024 and beyond.
   - Return the Completion Date in 'YYYY-MM-DD' format.
   - If you cannot determine the exact date from the input, ask the user specifically for the completion date.
   - When a relative time frame is given (e.g., "next week", "in two days"), calculate the exact date based on the current date, which is June 27, 2024.

2. Autocomplete:
   - The Autocomplete feature should automatically complete any abbreviated, slang, incomplete, or grammatically incorrect words in the user's input string.

3. Missing Information:
   - If any crucial information is missing from the user's input, ask for it once, focusing on the most essential details.
   - If after asking once, there's still not enough information, return 'Not enough details provided'.

4. Multiple Tasks:
   - If the user refers to multiple tasks in the input string, process each task separately and provide outputs for all tasks.

5. Professional Interaction:
   - Interact like an advanced, personalized AI assistant of 2024 and beyond.
   - Be efficient, professional, and thorough in your responses.
   - Avoid unnecessary pleasantries or filler phrases.

6. Clarification:
   - If any part of the input is ambiguous, seek clarification from the user before proceeding.

Remember, your primary goal is to accurately extract and process task information, with a particular focus on providing correct and precise completion dates. If you're unsure about any date-related information, always ask the user for confirmation or clarification.
"""
    )

def extract_information(user_input):
    """
    Extracts task information using LangChain LLM
    """
    prompt = create_prompt_template()
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
    formatted_prompt = prompt.format(input=str(user_input))
    
    logging.debug(f"Formatted prompt: {formatted_prompt}")

    try:
        output = llm.invoke(formatted_prompt)
        logging.debug(f"LLM Output: {output}")
        return output.content
    except Exception as e:
        logging.error(f"Error during LLM call: {e}")
        raise

def parse_extracted_info(extracted_text):
    """
    Parses the extracted information text into a dictionary
    """
    extracted_info_dict = {}
    for line in extracted_text.split('\n'):
        if ':' in line:
            key, value = line.strip().split(':', 1)
            extracted_info_dict[key.strip()] = value.strip()
    return extracted_info_dict

def is_information_complete(extracted_info_dict):
    """
    Checks if all required information fields are present and not 'unknown'
    """
    required_fields = ["Type", "Title", "Description", "Priority", "Completion Date"]
    return all(field in extracted_info_dict and extracted_info_dict[field].strip().lower() != 'unknown' for field in required_fields)

def create_task_response(task):
    """
    Creates a JSON response for a successfully extracted task
    """
    return jsonify({
        "type": "task",
        "data": {
            "type": task.type,
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "completion_date": task.completion_date
        }
    })

def create_message_response(message):
    """
    Creates a JSON response for a message (e.g., missing information)
    """
    return jsonify({
        "type": "message",
        "data": message
    })

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():
    return 'Hello, Elite Aider!'

@app.route('/get_task_types', methods=['GET'])
def get_task_types():
    """
    Returns a list of supported task types (example implementation)
    """
    task_types = [
        "Household Tasks",
        "Work/Professional Tasks",
        "Personal Tasks",
        "Errands",
        "Family and Social Tasks",
        "Health and Wellness",
        "Financial Tasks",
        "Educational/Skill Development",
        "Travel and Leisure",
        "Miscellaneous"
    ]
    return jsonify(task_types)

@app.route('/get_priority_options', methods=['GET'])
def get_priority_options():
    """
    Returns a list of available priority levels (example implementation)
    """
    priority_options = ["low", "medium", "high"]
    return jsonify(priority_options)

@app.route('/process_input', methods=['POST'])
def process_input():
    """
    Processes user input to extract task information
    """
    data = request.json
    conversation_history = data.get('conversation_history', [])
    user_input = data.get('user_input', {})

    logging.debug(f"Received user input: {user_input}")

    try:
        result = extract_information(user_input)
        extracted_info_dict = parse_extracted_info(result)

        logging.debug(f"Extracted info dict: {extracted_info_dict}")

        if is_information_complete(extracted_info_dict):
            task = Task(
                extracted_info_dict["Type"],
                extracted_info_dict["Title"],
                extracted_info_dict["Description"],
                extracted_info_dict["Priority"],
                extracted_info_dict["Completion Date"],
            )
            return create_task_response(task)
        else:
            missing_fields = [field for field in ["Type", "Title", "Description", "Priority", "Completion Date"] if field not in extracted_info_dict or extracted_info_dict[field].strip().lower() == 'unknown']
            return create_message_response(f"Please provide the following missing information: {', '.join(missing_fields)}")
    except Exception as e:
        logging.error(f"Error processing input: {e}")
        return create_message_response("An error occurred while processing your request. Please try again.")



