# Research Trailhead

An agentic AI web application that helps researchers identify novel, viable research directions by intelligently analyzing uploaded papers and autonomously exploring the research landscape.

## Features

### User Profile Creation
- **Manual Profile Creation**: Describe your research interests, background, and experience
- **Google Scholar Import**: Automatically import your research profile from Google Scholar
  - Scrapes publication history, h-index, research interests
  - Analyzes your research style and expertise level
  - Extracts research areas and specific topics

### Paper Analysis & Research Discovery
- Upload research papers (PDF format)
- AI-powered paper analysis using Google Gemini
- Automatic literature search and review
- **Persistent database storage** for all analyses and results
- Generates ranked, vetted research ideas with:
  - Novelty assessment
  - Doability evaluation
  - Literature synthesis
  - Suggested approaches
  - Key references with citations
- Query past analyses and retrieve historical research ideas

### User Experience
- Modern, responsive UI with landing page
- Interactive progress tracking
- Step-by-step workflow guidance
- Topic matching with user profile

## Setup

### Prerequisites

- Python 3.8+

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

### Workflow

1. **Create Your Profile**
   - Open `http://localhost:5001/ui_iterations/ui_6.html` in your browser
   - Choose between:
     - **Manual Description**: Enter your research interests, background, and experience level
     - **Google Scholar URL**: Import your profile automatically from Google Scholar
   - Click "Create Profile" to generate your research profile

2. **Upload Paper**
   - Upload a research paper (PDF format)
   - Select research topics from your profile (auto-detected or manually added)
   - Click "Upload & Analyze"

3. **Review Paper Analysis** (1-2 minutes)
   - Review paper summary and methodology
   - Explore key concepts and matched topics
   - Review generated research ideas (typically 5-10 ideas)

4. **Select Ideas for Research** (Select exactly 3)
   - Choose 3 research ideas that interest you
   - Click "Research Selected Ideas"

5. **Get Ranked Results** (2-5 minutes)
   - Explore the top 3 ranked research ideas
   - View novelty, doability, and topic match scores
   - Review literature synthesis and key references
   - Access full rationale and suggested approaches

## Project Structure

```
.
├── app.py                      # Flask backend with API endpoints
├── models.py                   # SQLAlchemy database models
├── database.py                 # Database connection management
├── index.html                  # Main UI
├── agents/
│   ├── profiler.py            # Profiler Agent (user profile analysis)
│   ├── reader.py              # Reader Agent (paper analysis)
│   └── searcher.py            # Searcher Agent (literature search & ranking)
├── utils/
│   ├── pdf_parser.py          # PDF text extraction
│   └── scholar_scraper.py     # Google Scholar profile scraping
├── ui_iterations/             # UI variations
│   ├── ui_6.html              # Latest UI with landing page and workflow
│   └── ...                    # Other UI iterations
├── alembic/                    # Database migrations
├── uploads/                    # Uploaded PDF storage
├── research_discovery.db       # SQLite database (auto-created)
└── requirements.txt           # Python dependencies
```

## Technology Stack

- **Backend:** Flask, Python
- **Database:** SQLite with SQLAlchemy ORM
- **Migrations:** Alembic
- **AI:** Google Gemini API
  - **ProfilerAgent & ReaderAgent:** Gemini 2.5 Flash (fast analysis)
  - **SearcherAgent:** Gemini 2.5 Pro (high-quality research synthesis)
- **Literature Search:** arXiv API
- **Google Scholar:** scholarly library for profile scraping
- **Frontend:** HTML, Tailwind CSS, Vanilla JavaScript
- **PDF Processing:** PyPDF2

## API Endpoints

### User Profile Endpoints
- `POST /api/users/profile` - Create user profile
  - Method: `manual` or `scholar`
  - For manual: `description`, `experience_level`
  - For scholar: `google_scholar_url`
- `GET /api/users/<user_id>/profile` - Get user profile
- `PUT /api/users/<user_id>/profile` - Update user profile

### Paper Analysis Endpoints
- `POST /api/upload` - Upload a research paper (PDF)
- `POST /api/analyze/read` - Start paper analysis (Reader Agent)
  - Returns: summary, methodology, concepts, research ideas
- `POST /api/analyze/search` - Research selected ideas (Searcher Agent)
  - Requires: `job_id`, `selected_ideas` (array of indices)
  - Returns: top 3 ranked ideas with full details

### Status & Results Endpoints
- `GET /api/papers` - List all uploaded papers
- `GET /api/analyses/<analysis_id>` - Get full analysis details with ideas and references
- `GET /api/papers/<paper_id>/analyses` - Get all analyses for a specific paper

## Database

The application uses SQLite for persistent storage of all data. The database schema consists of 5 main tables:

### Tables

1. **users** - Stores researcher profiles
   - User ID and timestamps
   - Manual description or Google Scholar URL
   - Scraped Google Scholar data (JSON)
   - AI-generated structured profile (JSON)
     - Expertise level, research areas, specific topics
     - Technical skills, research style, resource access
     - Publication count, h-index, preferences

2. **papers** - Stores uploaded research papers
   - Paper metadata (title, authors, year, venue, DOI)
   - PDF file information
   - Upload timestamp
   - Associated user ID

3. **analyses** - Stores paper analysis jobs and results
   - Analysis status and progress
   - Selected topics
   - Reader agent output (summary, concepts, findings, ideas)
   - Searcher agent output (ranked ideas, assessments)
   - Error messages
   - Associated user and paper IDs

4. **research_ideas** - Stores ranked research ideas
   - Idea rank (1, 2, 3)
   - Title, description, rationale
   - Scores (novelty, doability, topic match, composite)
   - Assessments (novelty, doability, literature synthesis)
   - Associated analysis ID

5. **references** - Stores literature references for each idea
   - Paper metadata (title, authors, year, venue)
   - Abstract and URL
   - Citation count
   - Relevance category
   - Summary
   - Associated research idea ID

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
- Landing page with parallax scrolling
- Interactive progress bar with step tracking
- Modern UI with dark green accent colors

## Additional Notes

### Experience Levels
Supported experience levels for manual profile creation:
- Undergraduate Student
- PhD Student
- Academia Researcher (combines Postdoc, Assistant Professor, Associate/Full Professor)
- Industry Researcher

### Google Scholar Import
When importing from Google Scholar:
- The system scrapes your publication history, h-index, and research interests
- It analyzes your research style based on publication patterns
- It extracts research areas from your publication venues and topics
- Processing typically takes 10-30 seconds depending on the number of publications

### Performance Considerations
- **Paper Analysis (Reader Agent)**: 1-2 minutes using Gemini 2.5 Flash
- **Research Ideas (Searcher Agent)**: 2-5 minutes using Gemini 2.5 Pro
- **Google Scholar Import**: 10-30 seconds (subject to rate limiting)
- Literature search uses arXiv API with automatic rate limiting

## License

[Add your license here]

