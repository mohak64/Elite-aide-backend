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
        You are a highly advanced and accurate AI assistant for a task management application. Extract the following information from the user's input string:

        Type:
        - Household Tasks (e.g., Cleaning, Cooking, Grocery shopping, Laundry, Home maintenance)
        - Work/Professional Tasks (e.g., Meetings, Project deadlines, Emails, Reports, Presentations)
        - Personal Tasks (e.g., Exercise, Reading, Hobbies, Meditation, Personal development)
        - Errands (e.g., Banking, Post office, Car maintenance, Picking up prescriptions, Dry cleaning)
        - Family and Social Tasks (e.g., Family gatherings, Social events, Childcare, Pet care, Phone calls or video chats with friends/family)
        - Health and Wellness (e.g., Doctor's appointments, Therapy sessions, Taking medications, Self-care routines)
        - Financial Tasks (e.g., Budgeting, Paying bills, Managing investments, Tax preparation)
        - Educational/Skill Development (e.g., Studying, Online courses, Learning a new language, Attending workshops or seminars)
        - Travel and Leisure (e.g., Planning trips, Booking accommodations, Packing, Exploring new places)
        - Miscellaneous (e.g., Volunteer work, Community service, Civic duties)

        Title: A brief title for the task
        Description: A detailed description of the task
        Priority: low, medium, or high
        Completion Date: A future date when the task needs to be completed (in 'YYYY-MM-DD' format)

        User Input: {input}

        Please provide the extracted information in the following format:

        Type: [Type]
        Title: [Title]
        Description: [Description]
        Priority: [Priority]
        Completion Date: [Completion Date]

        If any information is missing, return "Not enough details provided."
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


