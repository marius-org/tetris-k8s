from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

# Mount static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database connection from environment variables
def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "tetris"),
        user=os.getenv("DB_USER", "tetris"),
        password=os.getenv("DB_PASSWORD")
    )

# Create scores table if it doesn't exist
def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id SERIAL PRIMARY KEY,
                player VARCHAR(50) NOT NULL,
                score INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB init error: {e}")

# Run on startup
@app.on_event("startup")
def startup():
    init_db()

# Serve the game
@app.get("/")
def root():
    return FileResponse("static/index.html")

# Score model for request validation
class ScoreSubmit(BaseModel):
    player: str
    score: int

# Save a score
@app.post("/scores")
def save_score(data: ScoreSubmit):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO scores (player, score) VALUES (%s, %s)",
            (data.player, data.score)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Get top 10 scores
@app.get("/scores")
def get_scores():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT player, score, created_at FROM scores ORDER BY score DESC LIMIT 10"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"player": r[0], "score": r[1], "date": str(r[2])} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
