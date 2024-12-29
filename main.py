# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api import app as api_app
from db import init_db, test_connection
import logging
import os

# Create main FastAPI app
app = FastAPI()

# Get the absolute path to the project directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Mount the API under /api prefix
app.mount("/api", api_app)

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Serve index.html at root
@app.get("/")
async def read_root():
    return FileResponse(os.path.join(BASE_DIR, 'index.html'))

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    # Test database connection
    logger.info("Testing database connection...")
    if not test_connection():
        logger.error("Failed to connect to database. Please check your credentials.")
        exit(1)
    
    # Initialize the database
    logger.info("Initializing database...")
    init_db()
    
    # Run the application
    logger.info("Starting application...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)