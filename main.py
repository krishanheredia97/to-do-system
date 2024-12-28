# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api import app as api_app
from db import init_db, test_connection
import logging

# Create main FastAPI app
app = FastAPI()

# Mount the API under /api prefix
app.mount("/api", api_app)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html at root
@app.get("/")
async def read_root():
    return FileResponse('index.html')

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
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)