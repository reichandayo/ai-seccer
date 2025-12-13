
import os

services_content = r'''import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

class FootballDataService:
    def __init__(self):
        self.api_key = os.getenv("FOOTBALL_DATA_API_KEY")
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {"X-Auth-Token": self.api_key}

    def get_scheduled_matches(self):
        """Fetch scheduled matches with status SCHEDULED."""
        if not self.api_key:
            print("Warning: No API key found. Returning mock data.")
            return [
                {"id": 1001, "utcDate": "2025-12-14T15:00:00Z", "homeTeam": {"name": "Arsenal", "id": 57}, "awayTeam": {"name": "Chelsea", "id": 61}},
                {"id": 1002, "utcDate": "2025-12-14T17:30:00Z", "homeTeam": {"name": "Liverpool", "id": 64}, "awayTeam": {"name": "Man City", "id": 65}},
            ]
            
        url = f"{self.base_url}/matches"
        
        # Date filter: Today + 10 days
        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y-%m-%d")
        date_to = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")

        try:
            # Filter by scheduled status to avoid huge payloads
            # Competitions: 2021 (Premier League)
            params = {
                "status": "SCHEDULED", 
                "competitions": "2021",
                "dateFrom": today,
                "dateTo": date_to
            }
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("matches", [])
        except Exception as e:
            print(f"Error fetching matches: {e}")
            return []

    def get_match_details(self, match_id):
        """Fetch specific match details to get team IDs."""
        if not self.api_key or not match_id: 
            return None
            
        url = f"{self.base_url}/matches/{match_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 429:
                print("API Rate Limit Hit")
                return None
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching match details: {e}")
            return None

    def get_team_stats(self, team_id):
        """
        Fetch last 5 finished matches for a team to calculate stats.
        """
        if not self.api_key or not team_id:
            return {"name": "Team", "wins": 0, "draws": 0, "losses": 0, "avg_scored": 0, "avg_conceded": 0}

        url = f"{self.base_url}/teams/{team_id}/matches"
        try:
            # Fetch last 10 matches to get enough finished ones
            response = requests.get(
                url, 
                headers=self.headers, 
                params={"status": "FINISHED", "limit": 10},
                timeout=10
            )
            if response.status_code == 429:
                return {"error": "Rate limit exceeded"}
                
            response.raise_for_status()
            data = response.json()
            matches = data.get("matches", [])
            
            wins = 0
            draws = 0
            losses = 0
            goals_scored = 0
            goals_conceded = 0
            count = 0
            
            for m in matches:
                if count >= 5: break
                
                if m["score"]["fullTime"]["home"] is None:
                    continue

                is_home = (m["homeTeam"]["id"] == team_id)
                score_home = m["score"]["fullTime"]["home"]
                score_away = m["score"]["fullTime"]["away"]
                
                my_goals = score_home if is_home else score_away
                opp_goals = score_away if is_home else score_home
                
                goals_scored += my_goals
                goals_conceded += opp_goals
                
                if my_goals > opp_goals: wins += 1
                elif my_goals == opp_goals: draws += 1
                else: losses += 1
                count += 1
            
            if count == 0:
                 return {"name": data.get("name", "Team"), "wins": 0, "draws": 0, "losses": 0, "avg_scored": 0, "avg_conceded": 0}

            return {
                "name": data.get("name", "Team"),
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "avg_scored": round(goals_scored / count, 2),
                "avg_conceded": round(goals_conceded / count, 2)
            }
            
        except Exception as e:
            print(f"Error fetching team stats: {e}")
            return {"error": str(e)}


class PredictionService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    def predict_match(self, home_team, away_team, home_stats, away_stats):
        """
        Send match data to OpenAI to get a prediction.
        """
        if not self.api_key:
             return {
                "home_win": 40,
                "draw": 30,
                "away_win": 30,
                "analysis": "API key missing. Returning mock prediction. Home team seems strong."
            }

        prompt = f"""
        Predict the outcome of a football match between {home_team} (Home) and {away_team} (Away).
        
        Home Stats (Last 5): {json.dumps(home_stats)}
        Away Stats (Last 5): {json.dumps(away_stats)}
        
        Return a JSON object with keys: "home_win" (int %), "draw" (int %), "away_win" (int %), "analysis" (string).
        "analysis" MUST be written in Japanese.
        """
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a football expert assistant. return only JSON. Analysis must be in Japanese."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            content = response.choices[0].message.content
            start = content.find('{')
            end = content.rfind('}') + 1
            if start != -1 and end != -1:
                return json.loads(content[start:end])
            return json.loads(content)
            
        except Exception as e:
            print(f"Error predicting match: {e}")
            return {
                "home_win": 0, "draw": 0, "away_win": 0, 
                "analysis": f"prediction failed: {str(e)}"
            }
'''

main_content = r'''from fastapi import FastAPI, HTTPException, Query
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
'''


with open('services.py', 'w', encoding='utf-8') as f:
    f.write(services_content)
    
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_content)

env_content = "FOOTBALL_DATA_API_KEY=f9db336a66a349728a40ff2ac1b78502\nOPENAI_API_KEY=\n"
with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("Files restored successfully.")
