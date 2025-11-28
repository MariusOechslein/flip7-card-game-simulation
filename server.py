from fastapi import FastAPI
from flip7 import Game, AutomaticPlayer  # import your classes

app = FastAPI()

game: Game | None = None

@app.get("/") # = curl http://localhost:8000/
def start_game():
    global game
    players = [AutomaticPlayer(name="Marius"), AutomaticPlayer(name="Thea")]
    game = Game(players=players)
    game.play()
    return {"players": [{ 
        "name": p.name,
        "score": p.total_score,
    } for p in game.players]}

# Run: uv run uvicorn server:app --port 8000
