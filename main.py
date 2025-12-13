from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from services import FootballDataService, PredictionService
from pydantic import BaseModel
import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
football_service = FootballDataService()
prediction_service = PredictionService()

# Serve static files (Frontend)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "AI Soccer Prediction API is running. Go to /static/index.html"}

@app.get("/api/matches")
def get_matches():
    """Get list of scheduled matches."""
    matches = football_service.get_scheduled_matches()
    # Simplify response for frontend
    result = []
    for m in matches:
        result.append({
            "id": m["id"],
            "utcDate": m["utcDate"],
            "homeTeam": m["homeTeam"],
            "awayTeam": m["awayTeam"],
            "competition": m.get("competition", {}).get("name")
        })
    return result

@app.get("/api/predict")
def predict_match(
    home_team: str = Query(..., description="Name of the home team"),
    away_team: str = Query(..., description="Name of the away team"),
    match_id: int = Query(None, description="Optional match ID")
):
    """
    Predict match outcome. 
    """
    home_stats = {}
    away_stats = {}
    
    if match_id:
        details = football_service.get_match_details(match_id)
        if details:
            home_id = details['homeTeam']['id']
            away_id = details['awayTeam']['id']
            home_stats = football_service.get_team_stats(home_id)
            away_stats = football_service.get_team_stats(away_id)
        else:
            home_stats = {"name": home_team, "info": "Failed to fetch real stats"}
            away_stats = {"name": away_team, "info": "Failed to fetch real stats"}
    else:
         home_stats = {"name": home_team, "info": "No match ID provided"}
         away_stats = {"name": away_team, "info": "No match ID provided"}

    # 2. Call AI
    prediction = prediction_service.predict_match(
        home_team, 
        away_team, 
        home_stats, 
        away_stats
    )
    
    return {
        "match": f"{home_team} vs {away_team}",
        "prediction": prediction,
        "details": {
            "home_stats": home_stats,
            "away_stats": away_stats
        }
    }
