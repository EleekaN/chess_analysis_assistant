import openai
import requests
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import chess.pgn
from io import StringIO

# Initialize FastAPI
app = FastAPI()

# Lichess API Endpoint
LICHESS_API_URL = "https://lichess.org/api/cloud-eval"

# Define request body model for webhook
class WebhookRequest(BaseModel):
    pgn_text: str

from io import StringIO
import chess.pgn

from io import StringIO
import chess.pgn


def pgn_to_fen(pgn_text):
    """Parses PGN text and converts moves to FEN positions."""
    
    # 🔍 Step 1: Print raw PGN before passing to StringIO
    print("Raw PGN Received:\n", repr(pgn_text))  # Use repr() to check exact formatting

    # ✅ Step 2: Remove extra indentation and normalize newlines
    pgn_text = "\n".join(line.strip() for line in pgn_text.splitlines())  # Trim spaces
    print("Formatted PGN:\n", repr(pgn_text))  

    # ✅ Step 3: Pass cleaned PGN to StringIO
    pgn_io = StringIO(pgn_text)
    print("PGN Content in pgn_io:\n", pgn_io.getvalue())  

    # ✅ Step 4: Read PGN game
    game = chess.pgn.read_game(pgn_io)

    if game is None:
        print("❌ Error: PGN could not be read. Check formatting.")
        return []

    board = game.board()
    fen_positions = []

    # ✅ Step 5: Extract FEN positions
    for move in game.mainline_moves():
        board.push(move)
        fen_positions.append(board.fen())

    return fen_positions

@app.get("/")
def read_root():
    return {"message": "Chess Analysis webhook is running"}

@app.post("/webhook/analyze")
async def analyze_chess_game(request: WebhookRequest):
    try:
        pgn_text = request.pgn_text
                
        if not pgn_text:
            print("❌ Error: No PGN text received!")
            return {"error": "No PGN text provided"}
        
        #Convert pgn to fen
        fen_positions = pgn_to_fen(request.pgn_text)
        if not fen_positions:
            raise HTTPException(status_code=400, detail="Invalid PGN format.")
        # print("Generated FEN positions:", fen_positions)  # Debugging

        analysis_results = []
        for fen in fen_positions:
            print(f"Sending FEN to Lichess: {fen}")  # Debugging
            response = requests.get(f"{LICHESS_API_URL}?fen={fen}")
            # print("Lichess Response Code:", response.status_code)  # Debugging
            # print("Lichess Response Content:", response.text)  # Debugging

            if response.status_code == 200:
                lichess_response = {"analysis": [response.json()]}
                print(lichess_response)
                analysis_results.append(format_analysis_response(lichess_response))
        return {"analysis": analysis_results}

    except Exception as e:
        print("Error:", str(e))  # Debugging
        raise HTTPException(status_code=500, detail=str(e))


def format_analysis_response(lichess_response):
    """
    Extracts and structures Lichess evaluation data.
    """
    if "analysis" not in lichess_response:
        return {"error": "Invalid Lichess response format."}
    
    formatted_data = []
    
    for entry in lichess_response["analysis"]:
        fen = entry.get("fen", "Unknown FEN")
        pvs = entry.get("pvs", [])

        if isinstance(pvs, list) and pvs:
            best_move_data = pvs[0]  
            evaluation = best_move_data.get("cp", "Unknown")
            best_moves = best_move_data.get("moves", [])  
        else:
            evaluation = "Unknown"
            best_moves = []

        formatted_data.append({ 
            "fen": fen,
            "evaluation": evaluation,
            "depth": entry.get("depth", 0),
            "knodes": entry.get("knodes", 0),
            "best_move": best_moves[0] if best_moves else "No best move",
            "alternative_move": best_moves[1] if len(best_moves) > 1 else "No alternative",
            "mistake_move": best_moves[-1] if len(best_moves) > 2 else "No major mistake detected"
        })

    return formatted_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
