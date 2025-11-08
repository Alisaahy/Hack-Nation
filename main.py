from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="Hackathon Web App")

# CORS middleware (allow frontend to make API calls)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (CSS, JS, images)
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve frontend HTML
@app.get("/", response_class=HTMLResponse)
async def read_root():
    if os.path.exists("frontend/index.html"):
        with open("frontend/index.html", "r") as f:
            return f.read()
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hackathon App</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <h1>Welcome to Your Hackathon App!</h1>
        <p>Your FastAPI backend is running. Start building your app!</p>
        <p>API docs available at <a href="/docs">/docs</a></p>
    </body>
    </html>
    """

# Example API endpoint
@app.get("/api/hello")
async def hello():
    return {"message": "Hello from FastAPI backend!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

