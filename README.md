# Research Discovery Agent

An agentic AI web application that helps researchers identify novel, viable research directions by intelligently analyzing uploaded papers and autonomously exploring the research landscape.

## Features

- Upload research papers (PDF format)
- AI-powered paper analysis using Google Gemini
- Automatic literature search and review
- **Persistent database storage** for all analyses and results
- Generates 3 ranked, vetted research ideas with:
  - Novelty assessment
  - Doability evaluation
  - Literature synthesis
  - Suggested approaches
- Query past analyses and retrieve historical research ideas

## Setup

### Prerequisites

- Python 3.8+
- Google Gemini API key (get from https://makersuite.google.com/app/apikey)

### Installation

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

4. Initialize the database:
```bash
python database.py
```

5. Run the application:
```bash
python app.py
```

The app will be available at `http://localhost:5001`

**Note:** The database is automatically initialized when you run the app for the first time. A SQLite database file (`research_discovery.db`) will be created in the project root.

## Usage

1. Open `http://localhost:5001` in your browser
2. Upload a research paper (PDF)
3. Select research topics of interest
4. Click "Analyze Paper"
5. Wait 5-10 minutes for analysis
6. Explore the top 3 research ideas generated

## Project Structure

```
.
├── app.py                      # Flask backend with API endpoints
├── models.py                   # SQLAlchemy database models
├── database.py                 # Database connection management
├── index.html                  # Single-page UI
├── agents/
│   ├── reader.py              # Reader Agent (paper analysis)
│   └── searcher.py            # Searcher Agent (literature search & ranking)
├── utils/
│   └── pdf_parser.py          # PDF text extraction
├── alembic/                    # Database migrations
├── uploads/                    # Uploaded PDF storage
├── research_discovery.db       # SQLite database (auto-created)
└── requirements.txt           # Python dependencies
```

## Technology Stack

- **Backend:** Flask, Python
- **Database:** SQLite with SQLAlchemy ORM
- **Migrations:** Alembic
- **AI:** Google Gemini API (gemini-2.5-flash)
- **Literature Search:** Semantic Scholar API
- **Frontend:** HTML, Tailwind CSS, Vanilla JavaScript
- **PDF Processing:** PyPDF2

## API Endpoints

### Core Endpoints
- `POST /api/upload` - Upload a research paper
- `POST /api/analyze` - Start paper analysis
- `GET /api/status/<job_id>` - Check analysis status
- `GET /api/results/<job_id>` - Get final results

### Database Query Endpoints
- `GET /api/papers` - List all uploaded papers
- `GET /api/analyses/<analysis_id>` - Get full analysis details with ideas and references
- `GET /api/papers/<paper_id>/analyses` - Get all analyses for a specific paper

## Database

The application uses SQLite for persistent storage of all analysis data. The database schema consists of 4 main tables:

### Tables

1. **papers** - Stores uploaded research papers
   - Paper metadata (title, authors, year, venue, DOI)
   - PDF file information
   - Upload timestamp

2. **analyses** - Stores paper analysis jobs and results
   - Analysis status and progress
   - Selected topics
   - Reader agent output (summary, concepts, findings)
   - Searcher agent output
   - Error messages

3. **research_ideas** - Stores ranked research ideas
   - Idea rank (1, 2, 3)
   - Title, description, rationale
   - Scores (novelty, doability, topic match, composite)
   - Assessments (novelty, doability, literature synthesis)

4. **references** - Stores literature references for each idea
   - Paper metadata (title, authors, year, venue)
   - Abstract and URL
   - Citation count
   - Relevance category
   - Summary

### Database Management

**Initialize database:**
```bash
python database.py
```

**Run migrations:**
```bash
alembic upgrade head
```

**Create new migration after model changes:**
```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

**Reset database (warning: deletes all data):**
```python
from database import drop_db, init_db
drop_db()
init_db()
```

## Design

The UI follows a minimalist design with:
- 8pt spacing system
- 60-30-10 color ratio (white/gray/charcoal)
- Soft gradients and refined rounded corners
- WCAG-compliant contrast ratios
- Mobile-friendly responsive design

