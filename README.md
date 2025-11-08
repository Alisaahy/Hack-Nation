# Hackathon Web App

A Python web application with FastAPI backend and frontend.

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
uvicorn main:app --reload
```

The app will be available at `http://localhost:8000`

## Project Structure

```
.
├── main.py              # FastAPI application entry point
├── backend/             # Backend API routes and logic
├── frontend/            # Frontend static files (HTML, CSS, JS)
├── templates/           # Jinja2 templates (if using server-side rendering)
├── static/              # Static assets (CSS, JS, images)
└── requirements.txt     # Python dependencies
```

