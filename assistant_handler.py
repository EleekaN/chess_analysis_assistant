import openai
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI()

# 🔹 Replace with your Assistant ID from OpenAI
ASSISTANT_ID = "asst_p1IzmaD3EYsupjNI7nwuoqie"

# Webhook URL (update this after deploying on Render)
# WEBHOOK_URL = "https://chess-analysis-api.onrender.com/webhook/analyze"  # Change to your deployed URL when live

# def analyze_pgn(pgn_text):
#     """
#     Sends the PGN text to the FastAPI webhook for analysis and retrieves the response.
#     Formats the result like Lichess API response.
#     """
#     print(" 🔍 Sending PGN for analysis:\n", pgn_text)

#     try:
#         response = requests.post(WEBHOOK_URL, json={"pgn_text": pgn_text})
#         response.raise_for_status()
#         if response.status_code == 200:
#             lichess_response = response.json()
#             print(lichess_response) # debugging
#             return {"analysis": lichess_response}  
#         else:
#             return {"error": f"Failed to analyze PGN. Status Code: {response.status_code}"}

#     except Exception as e:
#         return {"error": str(e)}
    
# import openai
# import requests
# import json
# import time

# # OpenAI API Key (Make sure to set it as an environment variable)
# OPENAI_API_KEY = "your-openai-api-key"

# Render API Endpoint for Chess Analysis
API_URL = "https://chess-analysis-api.onrender.com/webhook/analyze"

def analyze_chess_game(pgn_text):
    """
    Sends a chess PGN to the Chess Analysis API for evaluation.
    """
    """
    Sends a PGN file to the Chess Analysis API and returns the result.
    """
    url = "https://chess-analysis-api.onrender.com/webhook/analyze"
    headers = {"Content-Type": "application/json"}
    payload = {"pgn_text": pgn_text}

    try:
        response = requests.post(API_URL, json=payload, headers= headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    
# Register the function for OpenAI Assistant
functions = [
    {
        "name": "analyze_chess_game",
        "description": "Analyze a chess game from PGN format and return insights.",
        "parameters": {
            "type": "object",
            "properties": {
                "pgn_text": {
                    "type": "string",
                    "description": "The PGN text of the chess game.",
                }
            },
            "required": ["pgn_text"],
        },
    }
]

# Create an OpenAI thread    
def create_thread():
    """ Creates a new thread for the assistant. """
    thread = client.beta.threads.create()
    return thread.id

# Run assistant with function calling
def run_assistant(pgn_text):
    thread_id = create_thread()

    # Send user message
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=f"Analyze this chess game: {pgn_text}",
    )

    # Run assistant
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=ASSISTANT_ID,
        instructions="Analyze the PGN file and provide key insights.",
        tools=[{"type": "function", "function": functions[0]}],
    )

    # Wait for assistant response
    while True:
        run_status = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        # check if a function call is required
        if run_status.status == 'requires_action':
            print("⚡ Function call detected! Executing...")

            # Extract function call details
            required_action = run_status.required_action
            tool_calls = required_action.submit_tool_outputs.tool_calls
            
            tool_outputs = []
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

            # function_call = required_action['submit_tool_outputs']['tool_calls'][0]
            # function_name = function_call["function"]["name"]
            # function_args = json.loads(function_call["function"]["arguments"])

                if function_name == 'analyze_chess_game':
                    output = analyze_chess_game(function_args["pgn_text"])

                    tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(output)  # Ensure JSON output format
                        })
                

            # Send the function output back to OpenAI
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs= [
                    {
                        "tool_call_id": tool_call.id,  # Get the tool call ID
                        "output": json.dumps(output)  # Send back your API response
                }
    ]
            )

        elif run_status.status == "completed":
            print("✅ Assistant execution completed.")
            break
        elif run_status.status == "failed":
            print("❌ Assistant execution failed.")
            return None
        time.sleep(2)  # Wait and check again

    # Retrieve messages from the thread
    messages = client.beta.threads.messages.list(thread_id=thread_id)
    return messages.data

# Example usage

if __name__ == "__main__":
    pgn_text = """[Event "Example Game"]
[Site "Lichess"]
[Date "2024.02.24"]
[Round "?"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7"""
# if __name__ == "__main__":
#     pgn_text = "Paste a valid PGN here"
    print("🎯 Creating thread...")
    print("📤 Sending message: Analyze this chess game")
    result = run_assistant(pgn_text)
    print("📝 Assistant Response:", result)

# def send_message(thread_id, message):
#     """ Sends a user message to the Assistant thread. """
#     client.beta.threads.messages.create(
#         thread_id=thread_id,
#         role="user",
#         content=message
#     )

# def run_assistant(thread_id):
#     """ Runs the Assistant on the specified thread. """
#     run = client.beta.threads.runs.create(
#         thread_id=thread_id,
#         assistant_id=ASSISTANT_ID
#     )
#     return run.id

# def process_assistant_response(thread_id, run_id):
#     """
#     Listens for the Assistant's function call and executes the appropriate function.
#     """
#     # openai.api_key = OPENAI_API_KEY

#     while True:
#         # Get the latest status of the run
#         run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        
#         if run.status == "completed":
#             print("✅ Assistant has completed execution.")
#             break
#         elif run.status == "failed":
#             print("❌ Assistant run failed:", run)
#             break
#         elif run.status == "requires_action":
#             # Extract function call details
#             tool_calls = run.required_action["submit_tool_outputs"]["tool_calls"]

#             tool_outputs = []
#             for tool in tool_calls:
#                 function_name = tool["function"]["name"]
#                 arguments = json.loads(tool["function"]["arguments"])

#                 if function_name == "analyze_chess_game":
#                     pgn_text = arguments["pgn_text"]
#                     result = analyze_chess_game(pgn_text)  # Call your API function
#                     tool_outputs.append({
#                         "tool_call_id": tool["id"],
#                         "output": json.dumps(result)  # Ensure JSON format
#                     })
            
#             # Sends the results back to OpenAI
#             client.beta.threads.runs.submit_tool_outputs(
#                 thread_id=thread_id,
#                 run_id=run_id,
#                 tool_outputs=tool_outputs
#             )

#         time.sleep(2)  # Wait before checking again

# def main():
#     """ Orchestrates the full process. """
#     print("🎯 Creating thread...")
#     thread_id = create_thread()

#     user_message = "Analyze this chess game: [Paste PGN here]"
#     print(f"📤 Sending message: {user_message}")
#     send_message(thread_id, user_message)

#     print("⚡ Running assistant...")
#     run_id = run_assistant(thread_id)

#     print("🕵️‍♂️ Checking function calls...")
#     process_assistant_response(thread_id, run_id)

# if __name__ == "__main__":
#     main()


# def handle_pgn_analysis(messages, model="gpt-4-turbo"):
#     """
#     Handles the OpenAI Assistant function call for PGN analysis.
#     - Extracts PGN from messages
#     - Calls `analyze_pgn`
#     - Returns response formatted like Lichess API output
#     """
#     try:
#         # Extract PGN from assistant's function call
#         for message in messages:
#             if "function_call" in message and message["function_call"]["name"] == "analyze_pgn":
#                 pgn_text = message["function_call"]["arguments"]["pgn_text"]
#                 break
#         else:
#             return {"error": "No PGN text found in function call."}

#         # Call analyze_pgn (FastAPI webhook)
#         analysis_result = analyze_pgn(pgn_text)

#         # Return response in Lichess API format to OpenAI
#         return {
#             "messages": messages + [{"role": "function", "name": "analyze_pgn", "content": analysis_result}],
#             "model": model
#         }

#     except Exception as e:
#         return {"error": str(e)}
    

# # Example test run
# if __name__ == "__main__":
#     sample_pgn = """
#     [Event "Example Game"]
#     [Site "Lichess"]
#     [Date "2024.02.24"]
#     [Round "?"]
#     [White "Player1"]
#     [Black "Player2"]
#     [Result "1-0"]

#     1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7
#     """

#     result = analyze_pgn(sample_pgn)
#     print("🔹 Analysis Result:\n", result)
