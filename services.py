import os
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
             # Basic mock data if no key for testing
            print("Warning: No API key found. Returning mock data.")
            return [
                {"id": 1001, "utcDate": "2025-12-14T15:00:00Z", "homeTeam": {"name": "Arsenal"}, "awayTeam": {"name": "Chelsea"}},
                {"id": 1002, "utcDate": "2025-12-14T17:30:00Z", "homeTeam": {"name": "Liverpool"}, "awayTeam": {"name": "Man City"}},
            ]
            
        url = f"{self.base_url}/matches"
        try:
            # Filter by scheduled status to avoid huge payloads
            response = requests.get(url, headers=self.headers, params={"status": "SCHEDULED"})
            response.raise_for_status()
            data = response.json()
            return data.get("matches", [])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching matches: {e}")
            return []

    def get_team_stats(self, team_id, team_name):
        """
        Fetch recent matches for a team to calculate stats.
        Since we might not have team_id easily from the match list in all cases without looking up,
        we might need to rely on what we get from match. 
        For MVP, let's mock the stats calculation or try to fetch if we have ID.
        """
        # MVP: Return mock stats or simplified calculation
        # In a real app, we would fetch /teams/{id}/matches?status=FINISHED
        return {
            "name": team_name,
            "wins": 3,
            "draws": 1,
            "losses": 1,
            "avg_scored": 1.8,
            "avg_conceded": 0.8
        }


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
        
        Home Stats (Last 5): {home_stats}
        Away Stats (Last 5): {away_stats}
        
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
            # meaningful cleanup to ensure json
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
