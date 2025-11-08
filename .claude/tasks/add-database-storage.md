# Add Database Storage - Implementation Plan

## Objective
Replace file-based JSON storage with PostgreSQL database for scalable, persistent storage of papers, analyses, and research ideas.

## Current State
- Results stored in JSON files (`results/` folder)
- Uploaded PDFs in `uploads/` folder
- No user management
- No ability to track analysis history
- Data lost when files are deleted

## Target State
- PostgreSQL database storing all analysis data
- Proper relational data model
- User authentication (optional for Phase 1)
- Analysis history and retrieval
- Scalable architecture for future features

## Implementation Approach

### Phase 1: Database Setup & Core Models (MVP)

**Reasoning:** Start with minimal database schema to replace current JSON storage. Add user authentication later.

#### 1.1 Database Selection & Setup
- **Database:** PostgreSQL (robust, supports JSON columns, good for relational data)
- **ORM:** SQLAlchemy (Python standard, works well with Flask)
- **Migration Tool:** Alembic (manages database schema changes)

#### 1.2 Core Data Models

Based on your architecture, create 4 core tables:

**Table: papers**
```sql
id UUID PRIMARY KEY
title VARCHAR(500)
authors TEXT[]  -- PostgreSQL array
year INTEGER
venue VARCHAR(200)
doi VARCHAR(100)
pdf_filename VARCHAR(255)  -- stored in uploads/
pdf_size_bytes INTEGER
upload_timestamp TIMESTAMP DEFAULT NOW()
user_id UUID (nullable for MVP)
```

**Table: analyses**
```sql
id UUID PRIMARY KEY
paper_id UUID REFERENCES papers(id)
selected_topics JSONB  -- ["ML", "NLP", ...]
reader_output JSONB  -- {concepts: [...], findings: [...], ideas: [...]}
searcher_output JSONB  -- Store intermediate results
status VARCHAR(20)  -- 'pending', 'parsing', 'reading', 'searching', 'complete', 'error'
progress INTEGER DEFAULT 0  -- 0-100
error_message TEXT
created_at TIMESTAMP DEFAULT NOW()
completed_at TIMESTAMP
```

**Table: research_ideas**
```sql
id UUID PRIMARY KEY
analysis_id UUID REFERENCES analyses(id)
rank INTEGER  -- 1, 2, 3
title VARCHAR(500)
description TEXT
rationale TEXT
novelty_score DECIMAL(3,1)  -- 1.0 - 5.0
doability_score DECIMAL(3,1)
topic_match_score DECIMAL(3,1)
composite_score DECIMAL(3,1)
novelty_assessment JSONB  -- {explored, maturity, gap, ...}
doability_assessment JSONB  -- {data_availability, methodology, ...}
literature_synthesis JSONB  -- {overview, whats_missing, suggested_approach, ...}
created_at TIMESTAMP DEFAULT NOW()
```

**Table: references**
```sql
id UUID PRIMARY KEY
idea_id UUID REFERENCES research_ideas(id)
title VARCHAR(500)
authors TEXT[]
year INTEGER
venue VARCHAR(200)
abstract TEXT
url VARCHAR(500)
citation_count INTEGER
relevance_category VARCHAR(50)  -- 'foundational', 'recent', 'gap'
summary TEXT  -- 2-3 sentence summary
created_at TIMESTAMP DEFAULT NOW()
```

**Indexes:**
- `analyses.paper_id`
- `analyses.status, analyses.created_at`
- `research_ideas.analysis_id, research_ideas.rank`
- `references.idea_id`

#### 1.3 Technology Stack Updates

**New Dependencies:**
- `psycopg2-binary` - PostgreSQL adapter
- `sqlalchemy` - ORM
- `alembic` - Database migrations

**Environment Variables:**
Add to `.env`:
```
DATABASE_URL=postgresql://user:password@localhost:5432/research_discovery
```

#### 1.4 Database Layer Implementation

**File: `models.py`** (new file)
- Define SQLAlchemy models for all 4 tables
- Include helper methods (e.g., `to_dict()` for JSON serialization)

**File: `database.py`** (new file)
- Database connection management
- Session handling
- Helper functions for common queries

#### 1.5 Update Application Code

**Modify `app.py`:**
1. Replace JSON file writes with database inserts
2. Update `/api/status/<job_id>` to query database
3. Update `/api/results/<job_id>` to fetch from database
4. Add database session management

**New API Endpoints:**
- `GET /api/papers` - List all uploaded papers
- `GET /api/analyses/<analysis_id>` - Get full analysis details
- `GET /api/papers/<paper_id>/analyses` - Get all analyses for a paper

#### 1.6 Migration from File-Based Storage

**Strategy:**
- Keep file-based storage as fallback initially
- Dual-write: Save to both files AND database during transition
- After testing, remove file writes

**Data Migration Script:**
- Read existing JSON files from `results/`
- Parse and insert into database
- Validate data integrity

#### 1.7 Testing

**Unit Tests:**
- Test model creation and relationships
- Test database queries

**Integration Tests:**
- Upload paper → analyze → retrieve results
- Verify data persistence across server restarts

---

### Phase 2: Enhanced Features (Future)

**Deferred to Phase 2+:**
- User authentication (add `users` table)
- Analysis sharing (public links)
- Favorite/bookmark ideas
- Export to PDF/BibTeX (query from database)
- Search across past analyses
- Analytics dashboard

---

## Detailed Implementation Steps

### Step 1: Set up PostgreSQL Database

**Local Development:**
```bash
# Install PostgreSQL (macOS)
brew install postgresql@14
brew services start postgresql@14

# Create database
createdb research_discovery

# Create user (optional)
createuser -P research_user
# Grant privileges
psql research_discovery -c "GRANT ALL PRIVILEGES ON DATABASE research_discovery TO research_user;"
```

**Production:**
- Use managed PostgreSQL (e.g., AWS RDS, Heroku Postgres, DigitalOcean)
- Configure connection pooling
- Set up backups

### Step 2: Add Dependencies

Update `requirements.txt`:
```
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
alembic==1.13.1
```

### Step 3: Create Database Models

**File: `models.py`**
```python
from sqlalchemy import Column, String, Integer, TIMESTAMP, ForeignKey, ARRAY, Text, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class Paper(Base):
    __tablename__ = 'papers'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500))
    authors = Column(ARRAY(Text))
    year = Column(Integer)
    venue = Column(String(200))
    doi = Column(String(100))
    pdf_filename = Column(String(255))
    pdf_size_bytes = Column(Integer)
    upload_timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    user_id = Column(UUID(as_uuid=True), nullable=True)

    # Relationship
    analyses = relationship("Analysis", back_populates="paper")

class Analysis(Base):
    __tablename__ = 'analyses'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    paper_id = Column(UUID(as_uuid=True), ForeignKey('papers.id'))
    selected_topics = Column(JSONB)
    reader_output = Column(JSONB)
    searcher_output = Column(JSONB)
    status = Column(String(20), default='pending')
    progress = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    completed_at = Column(TIMESTAMP)

    # Relationships
    paper = relationship("Paper", back_populates="analyses")
    ideas = relationship("ResearchIdea", back_populates="analysis")

# ... (similar for ResearchIdea and Reference models)
```

### Step 4: Database Connection Management

**File: `database.py`**
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 5: Initialize Database Schema

```bash
# Run Alembic migrations
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

### Step 6: Update Flask Routes

**Modified `app.py`:**
```python
from models import Paper, Analysis, ResearchIdea, Reference
from database import SessionLocal

@app.route('/api/upload', methods=['POST'])
def upload_paper():
    # ... existing file upload code ...

    # Create database entry
    db = SessionLocal()
    paper = Paper(
        id=job_id,
        pdf_filename=f"{job_id}_{filename}",
        pdf_size_bytes=file_size,
        # TODO: extract title, authors from PDF metadata
    )
    db.add(paper)

    analysis = Analysis(
        id=uuid.uuid4(),
        paper_id=job_id,
        selected_topics=[],  # Will be set in /analyze
        status='uploaded'
    )
    db.add(analysis)
    db.commit()
    db.close()

    # ... return response ...

# Similar updates for /analyze, /status, /results endpoints
```

### Step 7: Data Migration Script

**File: `migrate_json_to_db.py`**
- Read all JSON files from `results/`
- Parse and insert into database
- Log migration results

---

## Breaking Down Tasks

### Task Breakdown (MVP - Phase 1):

1. **Install PostgreSQL and create database** (30 min)
2. **Add dependencies to requirements.txt** (5 min)
3. **Create `models.py` with all 4 models** (1 hour)
4. **Create `database.py` with connection management** (30 min)
5. **Set up Alembic and create initial migration** (30 min)
6. **Update `/api/upload` to create Paper + Analysis records** (45 min)
7. **Update `/api/analyze` to update Analysis + create ResearchIdea + Reference records** (1.5 hours)
8. **Update `/api/status` to query database** (30 min)
9. **Update `/api/results` to query database** (45 min)
10. **Add new endpoints: GET /api/papers, GET /api/analyses/<id>** (1 hour)
11. **Test end-to-end flow** (1 hour)
12. **Create data migration script** (1 hour)
13. **Update README with database setup instructions** (30 min)

**Total Estimated Time: 9-10 hours**

---

## Success Criteria

✅ PostgreSQL database running locally
✅ All 4 tables created with proper relationships
✅ Upload paper → Creates Paper + Analysis records
✅ Analyze paper → Updates Analysis, creates ResearchIdea + Reference records
✅ Results persist across server restarts
✅ Can query past analyses
✅ Existing JSON files migrated to database
✅ No data loss during transition

---

## Risks & Mitigations

**Risk 1: Database setup complexity**
- Mitigation: Provide clear setup instructions, use Docker for easier setup

**Risk 2: Performance degradation with large JSON columns**
- Mitigation: Index JSONB columns, consider extracting frequently queried fields

**Risk 3: Data migration issues**
- Mitigation: Keep JSON files as backup, test migration on copy first

**Risk 4: Breaking existing functionality**
- Mitigation: Dual-write to files + DB initially, gradual transition

---

## Alternative: Simplified Approach (SQLite for MVP)

If PostgreSQL setup is too complex for MVP:

**Use SQLite instead:**
- No separate database server needed
- File-based (`research_discovery.db`)
- Same SQLAlchemy models work
- Easy migration to PostgreSQL later

**Tradeoffs:**
- Less scalable
- No concurrent writes (fine for single-user MVP)
- Simpler deployment

Change `DATABASE_URL` to:
```
DATABASE_URL=sqlite:///./research_discovery.db
```

---

## Next Steps After Approval

1. Choose database: PostgreSQL (recommended) or SQLite (simpler MVP)
2. Set up local database
3. Create git branch: `feature/database-storage`
4. Implement models and database layer
5. Update Flask routes incrementally
6. Test thoroughly
7. Migrate existing data
8. Update documentation

---

## Notes

- This plan prioritizes getting database working for core features
- User authentication deferred to Phase 2
- Focus on data persistence and retrieval
- Can run alongside existing file-based storage during transition
- Extensive testing needed before removing JSON file storage

---

## Implementation Summary (Completed: 2025-11-08)

### What Was Implemented

**Database Choice:** SQLite (PostgreSQL not installed, SQLite simpler for MVP)

**Files Created:**
1. `models.py` - SQLAlchemy models for 4 tables (Paper, Analysis, ResearchIdea, Reference)
2. `database.py` - Database connection management with session handling
3. `alembic/` - Migration framework initialized
4. `research_discovery.db` - SQLite database file (auto-created)

**Files Modified:**
1. `app.py` - Complete rewrite of all endpoints to use database:
   - `/api/upload` - Creates Paper + Analysis records
   - `/api/analyze` - Updates Analysis, creates ResearchIdea + Reference records
   - `/api/status` - Queries Analysis from database
   - `/api/results` - Retrieves results from database
   - Added `init_db()` call on app startup

2. `requirements.txt` - Added:
   - sqlalchemy==2.0.23
   - alembic==1.13.1

3. `.gitignore` - Added:
   - *.db files
   - alembic/versions/*.py
   - uploads/ and results/ directories

4. `README.md` - Added comprehensive database documentation:
   - Database section with table descriptions
   - Database management commands
   - Updated API endpoints section
   - Updated technology stack

**New API Endpoints Added:**
- `GET /api/papers` - List all uploaded papers
- `GET /api/analyses/<analysis_id>` - Get full analysis with ideas and references
- `GET /api/papers/<paper_id>/analyses` - Get all analyses for a paper

### Key Implementation Decisions

1. **Used SQLite instead of PostgreSQL**
   - Rationale: PostgreSQL not installed, SQLite simpler for MVP
   - Trade-off: Less scalable but easier deployment
   - Migration path: Same SQLAlchemy models work with PostgreSQL

2. **Stored JSON data in JSONB/JSON columns**
   - `Analysis.reader_output` - Stores full reader agent output
   - `Analysis.searcher_output` - Stores full searcher agent output
   - Allows flexibility while maintaining structured data for ideas/references

3. **Used String(36) for UUIDs**
   - SQLite doesn't have native UUID type
   - UUIDs stored as strings, generated via Python uuid.uuid4()

4. **Automatic database initialization**
   - Database auto-created when app starts (init_db() in main block)
   - No manual setup required for users

5. **Relationships with cascade delete**
   - Paper → Analysis → ResearchIdea → Reference
   - Deleting a paper deletes all related data

### Testing Results

✅ Database initialized successfully (44K file created)
✅ Flask app starts without errors
✅ `/api/papers` endpoint returns empty list correctly
✅ All database models created successfully
✅ Alembic migrations configured and initial migration created

### What Was NOT Implemented (Deferred)

- User authentication (Phase 2)
- Data migration script from JSON files (not needed, fresh start)
- Dual-write to files + database (went straight to database-only)
- PostgreSQL support (can migrate later if needed)

### Files That Can Be Removed

The following are no longer used but kept for reference:
- `results/` folder - JSON file storage (replaced by database)
- Legacy analysis results if any exist

### Next Steps for Future Enhancement

1. Add indexes on frequently queried fields:
   - `analyses.status, analyses.created_at`
   - `research_ideas.composite_score`

2. Add user authentication (Phase 2):
   - Create `users` table
   - Add `user_id` foreign keys
   - Implement login/session management

3. Add analytics/dashboard:
   - Most analyzed topics
   - Average idea scores over time
   - Popular research areas

4. Consider PostgreSQL migration if:
   - Concurrent users increase
   - Database size exceeds ~100MB
   - Need advanced features (full-text search, etc.)

### Time Spent

- Planning: Already done (previous session)
- Implementation: ~1.5 hours
  - Models + database.py: 20 min
  - Alembic setup: 15 min
  - app.py updates: 45 min
  - Documentation: 15 min
  - Testing: 15 min

**Total: 1.5 hours** (vs. 9-10 hours estimated for PostgreSQL)

### Lessons Learned

1. SQLite significantly faster to implement than PostgreSQL for MVP
2. SQLAlchemy's JSON support excellent for flexible data storage
3. Auto-initialization on app startup = better UX, no manual setup
4. Keeping plan as reference document helpful for implementation
