from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import openai
from typing import List
from pymongo import MongoClient
from bson import json_util  # Import the BSON library
# Create a FastAPI instance
application = FastAPI()

# Configure FastAPI to serve static files (e.g., CSS and JavaScript)
application.mount("/static", StaticFiles(directory="static"), name="static")

# Set your OpenAI API key here
openai.api_key = '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'

# # MongoDB configuration
# mongo_client = MongoClient("mongodb://localhost:27017/")  # Change this to your MongoDB server URL
# db = mongo_client["chatbot"]  # Replace "chatbot" with your database name
# collection = db["chat_history"]  # Replace "chat_history" with your collection name


mongo_host = 'localhost'  # Change to your MongoDB host
mongo_port = 27017  # Change to your MongoDB port
mongo_database = 'testmongo'  # Replace with your MongoDB database name
mongo_collection = 'collectionmongo'  # Replace with your desired collection name

client = MongoClient(f'mongodb://{mongo_host}:{mongo_port}/')
db = client[mongo_database]
collection = db[mongo_collection]

# Create a session variable for chat history (in-memory storage)
chat_history = []

# Configure templates directory for Jinja2
templates = Jinja2Templates(directory="templates")

# Function to save bot responses to MongoDB
def save_to_mongodb(role, content):
    chat_data = {"role": role, "content": content}
    collection.insert_one(chat_data)

# Route for the chat page
@application.get("/")
async def chat(request: Request):
    return templates.TemplateResponse("chat1.html", {"request": request})

# Route for getting bot responses
@application.get("/get_response/")
async def get_response(user_input: str = Query(None)):
    if user_input.strip() == "":
        return JSONResponse(content={"response": "Please enter a message."})

    global chat_history
    chat_history.append({'role': 'user', 'content': user_input})
    chat_history_string = "\n".join(f"{msg['role']}: {msg['content']}" for msg in chat_history)
    print('################', user_input)
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ]
        )
        bot_response = response['choices'][0]['message']['content']
        print('88888888', bot_response)

        # Save bot response to MongoDB
        save_to_mongodb('bot', bot_response)
    except Exception as e:
        bot_response = str(e)

    chat_history.append({'role': 'bot', 'content': bot_response})

    return JSONResponse(content={"response": bot_response})

import json
@application.get("/get_data/")
async def get_data(user_input: str = Query(None)):
    cursor = collection.find({})
    # Convert the cursor result to a list of dictionaries
    data = list(cursor)
    
     # Convert ObjectId to string representation for JSON serialization
    for item in data:
        if "_id" in item:
            item["_id"] = str(item["_id"])
    
    # Use json_util.dumps to convert BSON objects to JSON
    json_data = json.loads(json_util.dumps(data))
    
    # Format the JSON data with indentation for pretty printing
    pretty_json = json.dumps(json_data, indent=4)
    
    # Return the pretty JSON as a JSONResponse
    return JSONResponse(content=pretty_json, media_type="application/json")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=8000)
