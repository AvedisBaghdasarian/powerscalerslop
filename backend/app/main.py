from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from google import genai
import os
from datetime import datetime
import logging
from app.database import Database, BattleRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class Judgment(BaseModel):
    analysis: str
    narration: str
    winner: str

class BattleRequest(BaseModel):
    character1: str
    character2: str

class BattleResult(BaseModel):
    winner: str
    reasoning: str
    timestamp: datetime

class Server:
    def __init__(self):
        self.app = FastAPI(title="PowerScaler Battle Arena")
        self.db: Optional[Database] = None
        self.client: Optional[genai.Client] = None

        # Path configurations
        self.APP_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.BACKEND_BASE_DIR = os.path.dirname(self.APP_PACKAGE_DIR)
        self.FRONTEND_DIST_DIR = os.path.join(self.BACKEND_BASE_DIR, "frontend_dist")
        self.FRONTEND_ASSETS_DIR = os.path.join(self.FRONTEND_DIST_DIR, "assets")
        self.INDEX_HTML_FILE = os.path.join(self.FRONTEND_DIST_DIR, "index.html")

        self._log_path_info()
        self._configure_gemini_client()
        self._setup_middleware()
        self._setup_static_files()
        self._register_event_handlers()
        self._register_routes()

    def _log_path_info(self):
        logger.info(f"Expecting Svelte index.html at: {self.INDEX_HTML_FILE}")
        logger.info(f"Expecting Svelte assets at: {self.FRONTEND_ASSETS_DIR}")
        if not os.path.isdir(self.FRONTEND_ASSETS_DIR):
            logger.warning(f"Frontend assets directory NOT FOUND at: {self.FRONTEND_ASSETS_DIR}")
        if not os.path.isfile(self.INDEX_HTML_FILE):
            logger.warning(f"Frontend index.html NOT FOUND at: {self.INDEX_HTML_FILE}")

    def _configure_gemini_client(self):
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY not found in environment variables")
            # For tests, this might be an issue if GEMINI_API_KEY is not set and we don't mock early enough
            # However, our test_battle_endpoint specifically mocks genai.Client, so this block might not run in that test.
            try:
                is_pytest_running = "PYTEST_CURRENT_TEST" in os.environ
            except TypeError: # os.environ might not be fully populated in some restricted test envs
                is_pytest_running = False
            if not is_pytest_running: # Only raise if not in a test context where it might be mocked
                 raise ValueError("GEMINI_API_KEY environment variable is required")
            else:
                logger.warning("GEMINI_API_KEY not found, but running in test mode. Assuming genai.Client will be mocked.")
        if GEMINI_API_KEY: # Proceed if key is found
            self.client = genai.Client(api_key=GEMINI_API_KEY)
            logger.info("Gemini API configured successfully")
        # If no key and not mocked, self.client remains None, handled by route checks

    def _setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:5173"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_static_files(self):
        self.app.mount("/assets", StaticFiles(directory=self.FRONTEND_ASSETS_DIR), name="svelte-assets")

    def _register_event_handlers(self):
        @self.app.on_event("startup")
        async def startup_event():
            self.db = Database()
            logger.info("Database initialized and assigned to server instance.")

    async def serve_spa(self, full_path: str):
        if not os.path.isfile(self.INDEX_HTML_FILE):
            logger.error(f"SPA index.html cannot be served, file not found at: {self.INDEX_HTML_FILE}")
            raise HTTPException(status_code=404, detail="Client application not found.")
        return FileResponse(self.INDEX_HTML_FILE)

    async def create_battle(self, battle: BattleRequest):
        logger.info(f"Starting battle between {battle.character1} and {battle.character2}")
        
        if not self.client:
             logger.error("Gemini client not initialized for battle.")
             raise HTTPException(status_code=500, detail="Internal server error: Gemini client not ready.")
        if not self.db:
             logger.error("Database not initialized for battle.")
             raise HTTPException(status_code=500, detail="Internal server error: Database not ready.")

        try:
            logger.info("CREATE_BATTLE: Entered try block")
            logger.info(f"Analyzing {battle.character1}...")
            fighter1_analysis = self.client.models.generate_content(
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
            logger.info(f"CREATE_BATTLE: Fighter 1 analysis complete. Text: {fighter1_analysis.text[:50]}...")

            logger.info(f"Analyzing {battle.character2}...")
            fighter2_analysis = self.client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=f"""
                    {battle.character2} is up against {battle.character1}. You are on team {battle.character2}.
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
            logger.info(f"CREATE_BATTLE: Fighter 2 analysis complete. Text: {fighter2_analysis.text[:50]}...")

            logger.info("Getting final judgment...")
            judgment_response = self.client.models.generate_content(
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
                    "response_schema": Judgment,
                }
            )
            logger.info(f"CREATE_BATTLE: Judgment response complete. Text: {judgment_response.text[:50]}...")

            judgment_result = Judgment.model_validate_json(judgment_response.text)
            logger.info(f"CREATE_BATTLE: Judgment parsed. Winner: {judgment_result.winner}")

            result = BattleResult(
                winner=judgment_result.winner,
                reasoning=judgment_result.analysis,
                timestamp=datetime.now()
            )
            logger.info("CREATE_BATTLE: BattleResult created.")

            logger.info("Saving battle record to database...")
            battle_record = BattleRecord(
                character1=battle.character1,
                character2=battle.character2,
                winner=result.winner,
                reasoning=result.reasoning,
                timestamp=result.timestamp
            )
            self.db.save_battle(battle_record)
            logger.info("CREATE_BATTLE: Battle record saved.")

            return result
        except Exception as e:
            logger.error(f"CREATE_BATTLE: Error in battle creation: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    async def get_battle_history(self):
        if not self.db:
             logger.error("Database not initialized for battle history.")
             raise HTTPException(status_code=500, detail="Internal server error: Database not ready.")
        logger.info("Retrieving battle history...")
        try:
            history = self.db.get_battle_history()
            logger.info(f"Retrieved {len(history)} battle records")
            return history
        except Exception as e:
            logger.error(f"Error retrieving battle history: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    def _register_routes(self):
        self.app.add_api_route("/{full_path:path}", self.serve_spa, methods=["GET"])
        self.app.add_api_route("/battle", self.create_battle, methods=["POST"])
        self.app.add_api_route("/battle/history", self.get_battle_history, methods=["GET"])

# Instantiate the server and expose the app for Uvicorn
_server_instance = Server()
app = _server_instance.app 