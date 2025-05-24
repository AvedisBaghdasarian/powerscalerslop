import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime

# Models are needed for payload creation/assertion
from app.main import Judgment, BattleRequest, BattleResult 

# Global mock instance for the database
# This single instance will be returned by the mocked Database constructor
db_mock_instance = MagicMock()

# Patch the source Database class. When app.main.Server calls Database(), 
# it should get this mock if the import resolves to the patched version.
# However, we will also directly set _server_instance.db for robustness in tests.
@patch('app.database.Database', return_value=db_mock_instance)
def get_test_client_and_setup_db_mock(mock_db_class_at_source):
    """Imports app, directly sets the .db attribute on the server instance, and returns TestClient."""
    from app.main import _server_instance # Get the actual instance
    from app.main import app             # Get the FastAPI app object

    # Directly assign the mock instance to the server's db attribute.
    # This ensures that route handlers using self.db see the mock.
    _server_instance.db = db_mock_instance
    
    # The app's startup event @app.on_event("startup") self.db = Database() will still run
    # when TestClient initializes. If app.database.Database is correctly patched, it will assign
    # db_mock_instance again. Direct assignment above is a more forceful way for tests.
    
    return TestClient(app)

class TestBattleRoutes:
    
    def setup_method(self, method):
        """Reset the mock before each test and get a fresh client."""
        db_mock_instance.reset_mock() # Reset all interactions on the mock
        # Re-initialize specific method mocks if they were set globally on db_mock_instance by a previous test
        # For example, if a test did db_mock_instance.save_battle = MagicMock(), clear it or re-assign.
        # Often, it's better to assign method mocks within each test for clarity.
        self.client = get_test_client_and_setup_db_mock()

    def test_root(self):
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

    @patch('app.main.genai.Client')
    def test_battle_endpoint(self, mock_gemini_client_constructor):
        mock_gemini_instance = MagicMock()
        mock_gemini_client_constructor.return_value = mock_gemini_instance
        
        # Mock responses for the three calls to generate_content
        mock_fighter1_analysis_response = MagicMock()
        mock_fighter1_analysis_response.text = "Fighter 1 analysis text."

        mock_fighter2_analysis_response = MagicMock()
        mock_fighter2_analysis_response.text = "Fighter 2 analysis text."

        mock_judgment_payload = {
            "analysis": "Mocked final analysis for judgment",
            "narration": "Mocked final narration for judgment",
            "winner": "Character A" # This is what we expect
        }
        final_judgment_mock_response = MagicMock()
        final_judgment_mock_response.text = Judgment(**mock_judgment_payload).model_dump_json()

        # Set up side_effect to return these in order
        mock_gemini_instance.models.generate_content.side_effect = [
            mock_fighter1_analysis_response,
            mock_fighter2_analysis_response,
            final_judgment_mock_response
        ]

        db_mock_instance.save_battle = MagicMock()

        battle_payload = {"character1": "Character A", "character2": "Character B"}
        response = self.client.post("/battle", json=battle_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["winner"] == "Character A"
        # Update expected reasoning if it comes from the final judgment's analysis field
        assert data["reasoning"] == "Mocked final analysis for judgment"
        assert "timestamp" in data
        
        assert mock_gemini_instance.models.generate_content.call_count == 3
        db_mock_instance.save_battle.assert_called_once()

    def test_battle_history(self):
        mock_history_data = [
            {
                "character1": "Test1", "character2": "Test2", "winner": "Test1", 
                "reasoning": "Reason", "timestamp": datetime.now().isoformat()
            }
        ]
        # Configure the behavior of methods on our global db_mock_instance for this test
        db_mock_instance.get_battle_history = MagicMock(return_value=mock_history_data)

        response = self.client.get("/battle/history")
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["winner"] == "Test1"
        db_mock_instance.get_battle_history.assert_called_once() # Check the global mock instance

# To run these tests, ensure pytest and necessary mock libraries are installed.
# The @patch decorator at the class level applies to all methods in the class.
# Each test method will receive mock_db_class as an argument if it needs to interact with the class mock directly.
# The global db_mock is the instance that will be returned by Database() calls within the app. 