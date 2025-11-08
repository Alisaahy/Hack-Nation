# Personalized Research Discovery - Implementation Plan

## Enhanced User Experience

### Complete Flow
```
1. User Profile Creation
   ↓
2. Upload PDF → Read Paper (1-2 min)
   ↓
3. Get 10 personalized ideas based on user expertise
   ↓
4. User selects 3 ideas to research further
   ↓
5. Search & Rank (2-4 min) → Top 3 ranked by novelty & doability
   (considering user's research background)
```

## Phase 1: User Profiling System

### 1.1 User Profile Data Collection

**Two input methods:**

**Option A: Manual Description**
```
"Tell us about your research background:
- Your research area/expertise
- Key topics you're interested in
- Your experience level (PhD student, Postdoc, Professor, etc.)
- Notable publications or projects"
```

**Option B: Google Scholar Import**
```
"Enter your Google Scholar profile URL"
→ Scrape: publications, citations, co-authors, h-index, research interests
```

### 1.2 AI Profile Labeling

**Use Gemini to analyze and create structured profile:**
```json
{
  "user_id": "uuid",
  "expertise_level": "PhD Student" | "Postdoc" | "Professor" | "Industry",
  "research_areas": ["NLP", "Computer Vision", "Reinforcement Learning"],
  "specific_topics": ["Transformers", "Few-shot Learning", "Vision-Language Models"],
  "technical_skills": ["PyTorch", "HuggingFace", "Large-scale Training"],
  "publication_count": 5,
  "h_index": 3,
  "research_style": "Empirical" | "Theoretical" | "Applied",
  "resource_access": "Limited" | "Moderate" | "Extensive",
  "novelty_preference": 0.7,  // 0-1 scale
  "doability_preference": 0.8  // 0-1 scale
}
```

### 1.3 Database Schema Changes

**New table: `users`**
```python
class User(Base):
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Input data
    description = Column(Text)  # Manual description
    google_scholar_url = Column(String(500))
    google_scholar_data = Column(JSON)  # Scraped data

    # AI-generated profile
    profile = Column(JSON)  # Structured profile above

    # Relationships
    papers = relationship("Paper", back_populates="user")
```

**Update existing `Paper` model:**
```python
user_id = Column(String(36), ForeignKey('users.id'))
user = relationship("User", back_populates="papers")
```

**Update existing `Analysis` model:**
```python
# Add user context to analysis
user_profile_snapshot = Column(JSON)  # Snapshot of user profile at analysis time
```

## Phase 2: Personalized Idea Generation

### 2.1 Enhanced Reader Agent

**File: agents/reader.py**

**Modify `_generate_ideas()` method:**
```python
def _generate_ideas(self, paper_text, extraction, topics, user_profile):
    """
    Generate research ideas personalized to user's background

    Args:
        paper_text: Full paper text
        extraction: Extracted concepts/findings
        topics: Selected topics
        user_profile: User's research profile

    Returns:
        List of 10 personalized research ideas
    """
    prompt = f"""You are a research advisor. Based on this paper and the researcher's profile,
suggest 10 novel follow-up research ideas.

PAPER SUMMARY:
{extraction['summary']}

KEY CONCEPTS: {', '.join(extraction['concepts'])}

RESEARCHER PROFILE:
- Expertise Level: {user_profile['expertise_level']}
- Research Areas: {', '.join(user_profile['research_areas'])}
- Specific Topics: {', '.join(user_profile['specific_topics'])}
- Technical Skills: {', '.join(user_profile['technical_skills'])}
- Research Style: {user_profile['research_style']}
- Resource Access: {user_profile['resource_access']}

INSTRUCTIONS:
1. Tailor ideas to the researcher's expertise level
2. Align with their research areas and topics
3. Consider their technical skills (suggest methods they can implement)
4. Match their research style (empirical vs theoretical)
5. Consider resource constraints (data availability, compute needs)
6. Balance novelty with doability based on their background

For each idea, provide:
- title: Clear, specific research question
- description: 2-3 sentences on what and why
- rationale: Why this fits the researcher's profile
- required_skills: Skills needed (check against their profile)
- estimated_difficulty: "Feasible" | "Challenging" | "Ambitious" for this user
- estimated_timeline: "3-6 months" | "6-12 months" | "1-2 years"

Return JSON array of 10 ideas."""
```

### 2.2 Personalized Novelty & Doability Assessment

**File: agents/searcher.py**

**Modify `_assess_novelty()` method:**
```python
def _assess_novelty(self, idea, papers, user_profile):
    """
    Assess novelty considering user's publication history

    - If user has published in this area → higher novelty threshold
    - If user is new to area → moderate novelty acceptable
    - Compare against user's previous work
    """
    prompt = f"""Assess novelty of this research idea for THIS SPECIFIC RESEARCHER.

IDEA: {idea['title']}
{idea['description']}

RESEARCHER'S BACKGROUND:
- Research Areas: {user_profile['research_areas']}
- Previous Topics: {user_profile['specific_topics']}
- Publication Count: {user_profile.get('publication_count', 0)}

RECENT LITERATURE:
{format_papers(papers[:5])}

ASSESSMENT CRITERIA:
1. Novel relative to existing literature (general novelty)
2. Novel relative to researcher's previous work (personal novelty)
3. Appropriate novelty level for their expertise
   - PhD student: Incremental improvements acceptable
   - Senior researcher: Need more significant contributions

Return JSON:
{{
  "novelty_score": 1-5,
  "general_novelty": "description",
  "personal_novelty": "how different from their work",
  "novelty_level": "Incremental" | "Moderate" | "Significant" | "Breakthrough",
  "appropriateness": "Why this novelty level fits their career stage"
}}"""
```

**Modify `_assess_doability()` method:**
```python
def _assess_doability(self, idea, papers, user_profile):
    """
    Assess doability considering user's specific context

    - Check if user has required skills
    - Consider their resource access
    - Match to their typical project timeline
    - Account for their experience level
    """
    prompt = f"""Assess doability of this research idea for THIS SPECIFIC RESEARCHER.

IDEA: {idea['title']}
Required Skills: {idea.get('required_skills', [])}
Estimated Difficulty: {idea.get('estimated_difficulty', 'Unknown')}

RESEARCHER'S CONTEXT:
- Expertise Level: {user_profile['expertise_level']}
- Technical Skills: {user_profile['technical_skills']}
- Resource Access: {user_profile['resource_access']}
- H-index: {user_profile.get('h_index', 'N/A')}

ASSESSMENT CRITERIA:
1. Skill Match: Do they have the required technical skills?
2. Resource Feasibility: Can they access needed data/compute?
3. Time Realistic: Matches typical project timeline for their level?
4. Experience Appropriate: Not too ambitious or too simple?
5. Collaboration Needs: Do they need to find collaborators?

Return JSON:
{{
  "doability_score": 1-5,
  "skill_match": 0-1 (percentage of required skills they have),
  "resource_feasibility": "Easy" | "Moderate" | "Challenging",
  "timeline_estimate": "months",
  "main_challenges": ["challenge 1", "challenge 2"],
  "recommended_collaborations": ["expertise needed"],
  "next_steps": ["concrete first steps they can take"]
}}"""
```

### 2.3 Personalized Ranking

**Update composite score calculation:**
```python
# Adjust weights based on user preferences
novelty_weight = user_profile.get('novelty_preference', 0.3)
doability_weight = 1 - novelty_weight  # Inverse relationship

composite_score = (
    novelty_weight * novelty_assessment['novelty_score'] +
    doability_weight * doability_assessment['doability_score'] +
    0.2 * skill_match_bonus +  # Bonus for matching user's skills
    0.1 * personal_interest_score  # Bonus for matching user's stated interests
)
```

## Phase 3: Frontend Implementation

### 3.1 New Onboarding Flow

**Landing Page → User Profile Setup**

```html
<!-- Step 1: Welcome & Profile Setup -->
<div id="profile-setup" class="mb-32">
  <h2>Welcome to Research Discovery Agent</h2>
  <p>First, tell us about your research background</p>

  <!-- Tab switcher -->
  <div class="tabs">
    <button class="tab active" data-tab="manual">Manual Input</button>
    <button class="tab" data-tab="scholar">Google Scholar Import</button>
  </div>

  <!-- Manual Input Tab -->
  <div id="manual-tab" class="tab-content">
    <form id="manual-profile-form">
      <label>Research Background</label>
      <textarea
        placeholder="Describe your research area, expertise, interests..."
        rows="6"
      ></textarea>

      <label>Experience Level</label>
      <select>
        <option>Undergraduate Student</option>
        <option>PhD Student</option>
        <option>Postdoc</option>
        <option>Assistant Professor</option>
        <option>Associate/Full Professor</option>
        <option>Industry Researcher</option>
      </select>

      <button type="submit">Create Profile</button>
    </form>
  </div>

  <!-- Google Scholar Tab -->
  <div id="scholar-tab" class="tab-content hidden">
    <form id="scholar-profile-form">
      <label>Google Scholar Profile URL</label>
      <input
        type="url"
        placeholder="https://scholar.google.com/citations?user=..."
      />
      <p class="text-sm text-gray-600">
        We'll analyze your publications to understand your expertise
      </p>
      <button type="submit">Import from Scholar</button>
    </form>
  </div>

  <!-- Loading state -->
  <div id="profile-loading" class="hidden">
    <div class="spinner"></div>
    <p>Analyzing your research profile...</p>
  </div>

  <!-- Profile Preview -->
  <div id="profile-preview" class="hidden">
    <h3>Your Research Profile</h3>
    <div class="profile-card">
      <p><strong>Expertise Level:</strong> <span id="expertise"></span></p>
      <p><strong>Research Areas:</strong> <span id="areas"></span></p>
      <p><strong>Key Topics:</strong> <span id="topics"></span></p>
      <p><strong>Technical Skills:</strong> <span id="skills"></span></p>
    </div>
    <button id="confirm-profile">Looks Good! Continue</button>
    <button id="edit-profile">Edit Profile</button>
  </div>
</div>
```

### 3.2 Enhanced Ideas Display

**Show personalization details on each idea card:**

```html
<div class="idea-card">
  <input type="checkbox" checked />

  <div class="idea-header">
    <h3>{idea.title}</h3>
    <!-- Personalization badges -->
    <div class="badges">
      <span class="badge badge-green">Matches Your Skills</span>
      <span class="badge badge-blue">Aligns with Your Research</span>
    </div>
  </div>

  <p class="description">{idea.description}</p>

  <!-- Personalized insights -->
  <div class="personalized-info">
    <div class="info-row">
      <span class="label">Why for you:</span>
      <span class="value">{idea.rationale}</span>
    </div>
    <div class="info-row">
      <span class="label">Required skills:</span>
      <span class="value">{idea.required_skills}</span>
    </div>
    <div class="info-row">
      <span class="label">Estimated difficulty:</span>
      <span class="badge">{idea.estimated_difficulty}</span>
    </div>
    <div class="info-row">
      <span class="label">Timeline:</span>
      <span class="value">{idea.estimated_timeline}</span>
    </div>
  </div>
</div>
```

### 3.3 Enhanced Results Display

**Show personalized assessments in final results:**

```html
<div class="result-card">
  <div class="rank-badge">Rank #{rank}</div>
  <h2>{idea.title}</h2>

  <!-- Scores with context -->
  <div class="scores">
    <div class="score">
      <span class="label">Novelty</span>
      <div class="stars">{novelty_score}/5</div>
      <span class="context">{novelty_level} - {appropriateness}</span>
    </div>
    <div class="score">
      <span class="label">Doability</span>
      <div class="stars">{doability_score}/5</div>
      <span class="context">
        {skill_match}% skill match • {resource_feasibility} resources
      </span>
    </div>
  </div>

  <!-- Personalized recommendations -->
  <div class="recommendations">
    <h4>Next Steps for You:</h4>
    <ul>
      {#each next_steps}
        <li>{step}</li>
      {/each}
    </ul>

    {#if recommended_collaborations.length}
    <h4>Consider Collaborating With:</h4>
    <ul>
      {#each recommended_collaborations}
        <li>{expertise}</li>
      {/each}
    </ul>
    {/if}
  </div>
</div>
```

## Phase 4: API Implementation

### 4.1 New Endpoints

**User Profile Management:**
```python
POST /api/users/profile
{
  "method": "manual" | "scholar",
  "description": "text" (if manual),
  "google_scholar_url": "url" (if scholar)
}
→ Returns: { "user_id": "uuid", "profile": {...} }

GET /api/users/{user_id}/profile
→ Returns: { "profile": {...} }

PUT /api/users/{user_id}/profile
→ Update profile
```

**Updated Analysis Endpoints:**
```python
POST /api/upload
{
  "file": file,
  "user_id": "uuid"  // NEW: Associate with user
}

POST /api/analyze
{
  "job_id": "uuid",
  "topics": ["ML", "NLP"],
  "user_id": "uuid"  // NEW: Use for personalization
}

POST /api/search
{
  "analysis_id": "uuid",
  "selected_idea_ids": [0, 2, 5],
  "user_id": "uuid"  // NEW: For personalized ranking
}
```

### 4.2 Google Scholar Scraping

**New file: `utils/scholar_scraper.py`**
```python
import requests
from bs4 import BeautifulSoup

def scrape_scholar_profile(profile_url):
    """
    Scrape Google Scholar profile
    Returns: {
        "name": str,
        "affiliation": str,
        "interests": [str],
        "publications": [{title, year, citations, venue}],
        "h_index": int,
        "i10_index": int,
        "total_citations": int
    }
    """
    # Implementation with requests + BeautifulSoup
    # Or use scholarly library: pip install scholarly
```

**Alternative: Use Semantic Scholar API**
```python
def get_author_from_semantic_scholar(author_name):
    """
    Use Semantic Scholar API to get author profile
    More reliable than scraping
    """
    url = f"https://api.semanticscholar.org/graph/v1/author/search?query={author_name}"
    # Get publications, fields, h-index
```

### 4.3 Profile Analysis Agent

**New file: `agents/profiler.py`**
```python
class ProfilerAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze_manual_description(self, description, experience_level):
        """
        Analyze manual text description and extract structured profile
        """
        prompt = f"""Analyze this researcher's description and create a structured profile.

DESCRIPTION:
{description}

EXPERIENCE LEVEL: {experience_level}

Extract and return JSON:
{{
  "expertise_level": "{experience_level}",
  "research_areas": ["area1", "area2"],  // Broad areas (3-5)
  "specific_topics": ["topic1", "topic2"],  // Specific topics (5-10)
  "technical_skills": ["skill1", "skill2"],  // Technical skills mentioned
  "research_style": "Empirical" | "Theoretical" | "Applied",
  "resource_access": "Limited" | "Moderate" | "Extensive",
  "novelty_preference": 0-1,  // Infer from description
  "doability_preference": 0-1  // Infer from description
}}"""

        response = self.model.generate_content(prompt)
        return parse_json(response.text)

    def analyze_scholar_data(self, scholar_data):
        """
        Analyze Google Scholar data and create structured profile
        """
        prompt = f"""Analyze this researcher's publication record and create a structured profile.

PUBLICATIONS: {scholar_data['publications'][:10]}  // Recent 10
H-INDEX: {scholar_data['h_index']}
STATED INTERESTS: {scholar_data['interests']}
TOTAL CITATIONS: {scholar_data['total_citations']}

Infer and return JSON:
{{
  "expertise_level": "PhD Student" | "Postdoc" | "Professor",  // Infer from h-index, pub count
  "research_areas": [...],  // From publication venues/topics
  "specific_topics": [...],  // From paper titles/abstracts
  "technical_skills": [...],  // Infer from methodologies used
  "research_style": "Empirical" | "Theoretical" | "Applied",
  "resource_access": "Limited" | "Moderate" | "Extensive",  // Infer from affiliation
  "publication_count": {scholar_data['publication_count']},
  "h_index": {scholar_data['h_index']},
  "novelty_preference": 0-1,  // Infer from publication pattern
  "doability_preference": 0-1
}}"""

        response = self.model.generate_content(prompt)
        return parse_json(response.text)
```

## Implementation Order

### Sprint 1: Database & User Profile (2-3 hours)
1. Add `users` table to models.py
2. Create database migration
3. Implement `/api/users/profile` endpoint (manual description only)
4. Create ProfilerAgent for text analysis
5. Test profile creation

### Sprint 2: Personalized Reader Agent (2-3 hours)
1. Update Reader Agent to accept user_profile parameter
2. Modify idea generation prompt with personalization
3. Update `/api/analyze` to use user profile
4. Test personalized idea generation

### Sprint 3: Split Read/Search Workflow (2-3 hours)
1. Modify `/api/analyze` to stop after Reader Agent
2. Create new `/api/search` endpoint
3. Update status flow (add `ideas_ready`)
4. Test two-phase workflow

### Sprint 4: Personalized Searcher Agent (2-3 hours)
1. Update Searcher Agent assessments with user context
2. Implement personalized ranking
3. Update results formatting
4. Test end-to-end personalization

### Sprint 5: Frontend - Profile Setup (3-4 hours)
1. Create profile setup page/modal
2. Implement manual description form
3. Profile preview component
4. Connect to backend API
5. Save user_id in session/localStorage

### Sprint 6: Frontend - Personalized Ideas (2-3 hours)
1. Update idea cards with personalization info
2. Add difficulty/timeline badges
3. Show "why for you" rationale
4. Test idea selection flow

### Sprint 7: Frontend - Enhanced Results (2-3 hours)
1. Update results display with personalized assessments
2. Add "next steps" section
3. Add collaboration recommendations
4. Polish UI/UX

### Sprint 8: Google Scholar Integration (Optional, 2-3 hours)
1. Implement scholar scraping (or Semantic Scholar API)
2. Add scholar import form
3. Test scholar-based profile creation

## MVP Scope for Initial Implementation

**Phase 1 MVP: Manual Profile + Basic Personalization**
- Manual description input only (skip Google Scholar for now)
- Basic profiler agent (extract areas, topics, skills)
- Personalized idea generation (tailor to user background)
- Personalized doability assessment (skill matching)
- Simple ranking adjustment based on profile

**Can add later:**
- Google Scholar import
- Advanced novelty assessment with personal publication history
- Collaboration recommendations
- Profile editing/refinement
- Multiple user profiles

## Testing Strategy

1. **Test Profile Creation**
   - Input: "I'm a PhD student working on transformers for NLP. I have experience with PyTorch and HuggingFace."
   - Expected: Profile with NLP research area, transformer topic, PyTorch skill

2. **Test Personalized Ideas**
   - User: Junior PhD student in NLP
   - Paper: Attention Is All You Need
   - Expected: Ideas should be feasible, align with NLP/transformers, mention PyTorch

3. **Test Doability Assessment**
   - Idea requiring "experience with distributed training"
   - User without that skill → lower doability score
   - User with that skill → higher doability score

4. **Test End-to-End Flow**
   - Create profile → Upload paper → Review 10 personalized ideas →
   - Select 3 → Search & rank → Verify top 3 are appropriate for user
