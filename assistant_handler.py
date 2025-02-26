import openai
import requests

# Webhook URL (update this after deploying on Render)
WEBHOOK_URL = "http://localhost:8000/webhook/analyze"  # Change to your deployed URL when live

def analyze_pgn(pgn_text):
    """
    Sends the PGN text to the FastAPI webhook for analysis and retrieves the response.
    Formats the result like Lichess API response.
    """
    print("🔍 Sending PGN for analysis:\n", pgn_text)

    try:
        response = requests.post(WEBHOOK_URL, json={"pgn_text": pgn_text})
        if response.status_code == 200:
            lichess_response = response.json()
            print(lichess_response) # debugging
            return {"analysis": lichess_response}  
        else:
            return {"error": f"Failed to analyze PGN. Status Code: {response.status_code}"}

    except Exception as e:
        return {"error": str(e)}

def handle_pgn_analysis(messages, model="gpt-4-turbo"):
    """
    Handles the OpenAI Assistant function call for PGN analysis.
    - Extracts PGN from messages
    - Calls `analyze_pgn`
    - Returns response formatted like Lichess API output
    """
    try:
        # Extract PGN from assistant's function call
        for message in messages:
            if "function_call" in message and message["function_call"]["name"] == "analyze_pgn":
                pgn_text = message["function_call"]["arguments"]["pgn_text"]
                break
        else:
            return {"error": "No PGN text found in function call."}

        # Call analyze_pgn (FastAPI webhook)
        analysis_result = analyze_pgn(pgn_text)

        # Return response in Lichess API format to OpenAI
        return {
            "messages": messages + [{"role": "function", "name": "analyze_pgn", "content": analysis_result}],
            "model": model
        }

    except Exception as e:
        return {"error": str(e)}
    

# Example test run
if __name__ == "__main__":
    sample_pgn = """
    [Event "Example Game"]
    [Site "Lichess"]
    [Date "2024.02.24"]
    [Round "?"]
    [White "Player1"]
    [Black "Player2"]
    [Result "1-0"]

    1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7
    """

    result = analyze_pgn(sample_pgn)
    print("🔹 Analysis Result:\n", result)
