import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from db import init_db, get_db

async def main():
    init_db()
    db = get_db()
    
    leagues = await db.leagues.find({}, {'_id': 0}).to_list(5)
    teams = await db.teams.find({}, {'_id': 0}).to_list(5)
    games = await db.games.find({}, {'_id': 0}).to_list(5)
    users = await db.users.count_documents({})
    
    print(f"✓ Leagues: {len(leagues)}")
    print(f"✓ Teams: {len(teams)}")
    print(f"✓ Games: {len(games)}")
    print(f"✓ Users: {users}")
    
    if games:
        g = games[0]
        print(f"\nSample game: {g.get('id')} | {g.get('home_team_id')} vs {g.get('away_team_id')} | {g.get('status')}")

asyncio.run(main())
