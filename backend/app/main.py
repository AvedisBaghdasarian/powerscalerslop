from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from google import genai
import os
from datetime import datetime
import logging
from app.database import Database, BattleRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Determine paths for frontend assets
# Assumes main.py is in a directory like '.../backend_project_root/app/main.py'
# and frontend assets are copied to '.../backend_project_root/frontend_dist/'
# In Docker, if main.py is at /app/app/main.py, this expects frontend at /app/frontend_dist/
APP_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__)) # Directory of main.py (e.g., /app/app)
BACKEND_BASE_DIR = os.path.dirname(APP_PACKAGE_DIR) # Parent of app package dir (e.g., /app)

FRONTEND_DIST_DIR = os.path.join(BACKEND_BASE_DIR, "frontend_dist")
FRONTEND_ASSETS_DIR = os.path.join(FRONTEND_DIST_DIR, "assets")
INDEX_HTML_FILE = os.path.join(FRONTEND_DIST_DIR, "index.html")

logger.info(f"Expecting Svelte index.html at: {INDEX_HTML_FILE}")
logger.info(f"Expecting Svelte assets at: {FRONTEND_ASSETS_DIR}")

if not os.path.isdir(FRONTEND_ASSETS_DIR):
    logger.warning(f"Frontend assets directory NOT FOUND at: {FRONTEND_ASSETS_DIR}")
if not os.path.isfile(INDEX_HTML_FILE):
    logger.warning(f"Frontend index.html NOT FOUND at: {INDEX_HTML_FILE}")

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    raise ValueError("GEMINI_API_KEY environment variable is required")

client = genai.Client(api_key=GEMINI_API_KEY)
logger.info("Gemini API configured successfully")

app = FastAPI(title="PowerScaler Battle Arena")

# Mount static files for the new Svelte frontend
app.mount("/assets", StaticFiles(directory=FRONTEND_ASSETS_DIR), name="svelte-assets")

# Comment out or remove the old static files mount if no longer needed
# app.mount("/static", StaticFiles(directory="app/static"), name="static")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Kept for local Svelte dev, review for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Judgment(BaseModel):
    analysis: List[str]
    narration: str
    winner: str

# Initialize database
db = None

@app.on_event("startup")
async def startup_event():
    global db
    db = Database()

class BattleRequest(BaseModel):
    character1: str
    character2: str

class BattleResult(BaseModel):
    winner: str
    reasoning: str
    timestamp: datetime

# Serve the Svelte app's index.html for the root path and any other non-API paths
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    if not os.path.isfile(INDEX_HTML_FILE):
        logger.error(f"SPA index.html cannot be served, file not found at: {INDEX_HTML_FILE}")
        raise HTTPException(status_code=404, detail="Client application not found.")
    return FileResponse(INDEX_HTML_FILE)

@app.post("/battle")
async def create_battle(battle: BattleRequest):
    logger.info(f"Starting battle between {battle.character1} and {battle.character2}")
    try:
        # Get character analysis from fighters
        logger.info(f"Analyzing {battle.character1}...")
        fighter1_analysis = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=f"""
        {battle.character1} is up against {battle.character2}. You are on team {battle.character1}. 
        Consider the following, among other things: hax, power vs. fragility, hit‑capability, attrition, special abilities, tactics, narrative.
        write a narrative of what you believe will happen in the battle based on that analysis.
        Explicitly anticipate {battle.character2}'s best argument and battle narrative and explain why it fails inconsistant.
        Anchor necessary claims with at least one concrete, canon feat (e.g. "demolished a mountain in 0.2 s").
        
        The most important thing here is to identify the most narratively consistent and likely situation to play out.
        do not attempt to qualitatively bring disparate fighters closer in power. If one character is too durable to be hurt by the other, then consider that.
        if one character is too fast to hit the other, than consider that.
        if one character has a special power that has no answer, then consider that.
        consider the scale of attacks that hurt each character and understand if each characters attacks meet that scale (ie blowing up planets)
        if necessary, consider if these ideas are backed up by feats, or canon narrative events
        feel free to chain scale feats of other characters in their verse

        keep points short and sweet. Use bullet points and no fluff
        """
        )

        logger.info(f"Analysis for {battle.character1} complete")

        logger.info(f"Analyzing {battle.character2}...")
        fighter2_analysis = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=f"""
        {battle.character2} is up against {battle.character1}. You are on team {battle.character1}. 
        Consider the following, among other things: hax, power vs. fragility, hit‑capability, attrition, special abilities, tactics, narrative.
        write a narrative of what you believe will happen in the battle based on that analysis.
        Explicitly anticipate {battle.character1}'s best argument and battle narrative and explain why it fails inconsistant.
        Anchor necessary claims with at least one concrete, canon feat (e.g. "demolished a mountain in 0.2 s").

        The most important thing here is to identify the most narratively consistent and likely situation to play out.
        do not attempt to qualitatively bring disparate fighters closer in power. If one character is too durable to be hurt by the other, then consider that.
        if one character is too fast to hit the other, than consider that.
        if one character has a special power that has no answer, then consider that.
        consider the scale of attacks that hurt each character and understand if each characters attacks meet that scale (ie blowing up planets)
        if necessary, consider if these ideas are backed up by feats, or canon narrative events

        feel free to chain scale feats of other characters in their verse

        keep points short and sweet. Use bullet points and no fluff
        """
        )

        logger.info(f"Analysis for {battle.character2} complete")

        # Get final judgment
        logger.info("Getting final judgment...")

        judgment = client.models.generate_content(
            model="gemini-2.0-flash-lite",
            contents=f"""    
        You are the judge of a powerscaling theoretical battle. Take these two arguments and narraties of how a battle will play out and determine who wins and why.
        Here are some potential

        The most important thing here is to identify the most narratively consistent and likely situation to play out.
        do not attempt to qualitatively bring disparate fighters closer in power. If one character is too durable to be hurt by the other, then consider that.
        if one character is too fast to hit the other, than consider that.
        if one character has a special power that has no answer, then consider that.
        consider the scale of attacks that hurt each character and understand if each characters attacks meet that scale (ie blowing up planets)
        if necessary, consider if these ideas are backed up by feats, or canon narrative events

        Here are some other things to consider: 
        • At each step, call out any unsupported or contradictory claims.  
        • Stop as soon as one fighter clearly "outranks" the other.  
        • If neither gains a clear win, note it as a draw or invoke narrative logic as a tie‑breaker.  

        Based on that, who wins and why? Provide detailed, tier‑free reasoning and flag any inconsistency or missing feat evidence.
        keep points short and sweet. Use bullet points and no fluff

        – Analysis for {battle.character1} –  
        {fighter1_analysis.text}

        – Analysis for {battle.character2} –  
        {fighter2_analysis.text}

        Output only a JSON object conforming to the Judgment schema.

        The analysis should reflect the most logical analysis. This should be markdown formatted if necessary.
        The narrative to should be a short narrative of the most logical battle. this should be markdown formatted if necessary.
        The winner should be the character that wins the battle.
        """,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[Judgment],
            }
        )
        logger.info("Judgment received")

        # Determine winner
        winner = battle.character1 if "wins" in judgment.text.lower() else battle.character2
        logger.info(f"Winner determined: {winner}")

        result = BattleResult(
            winner=winner,
            reasoning=judgment.text,
            timestamp=datetime.now()
        )

        # Store result in MongoDB
        logger.info("Saving battle record to database...")
        battle_record = BattleRecord(
            character1=battle.character1,
            character2=battle.character2,
            winner=result.winner,
            reasoning=result.reasoning,
            timestamp=result.timestamp
        )
        db.save_battle(battle_record)
        logger.info("Battle record saved successfully")

        return result
    except Exception as e:
        logger.error(f"Error in battle creation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/battle/history")
async def get_battle_history():
    logger.info("Retrieving battle history...")
    try:
        history = db.get_battle_history()
        logger.info(f"Retrieved {len(history)} battle records")
        return history
    except Exception as e:
        logger.error(f"Error retrieving battle history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 