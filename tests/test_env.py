import os
from dotenv import load_dotenv
import logging

def test_env_loading():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Get the path to .env file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(current_dir, '..', 'backend')
    env_path = os.path.join(backend_dir, '.env')
    
    logger.info(f"Testing .env loading from: {env_path}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Directory contents: {os.listdir(backend_dir)}")
    
    # Try to load the .env file
    load_dotenv(env_path)
    
    # Check if GEMINI_API_KEY exists
    api_key = os.getenv("GEMINI_API_KEY")
    logger.info(f"GEMINI_API_KEY exists: {api_key is not None}")
    logger.info(f"GEMINI_API_KEY length: {len(api_key) if api_key else 0}")
    
    # Assert that the API key exists
    assert api_key is not None, "GEMINI_API_KEY not found in .env file"
    assert len(api_key) > 0, "GEMINI_API_KEY is empty"

if __name__ == "__main__":
    test_env_loading() 