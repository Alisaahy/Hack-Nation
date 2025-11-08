# Split Read and Search Workflow

## Objective
Separate the Reader and Searcher agent tasks so users can:
1. Upload paper → Get research ideas from Reader Agent immediately (1-2 min)
2. Review ideas and select which ones to research further
3. Click "Search & Rank Selected Ideas" → Searcher Agent processes only selected ideas (2-4 min)

This improves UX by:
- Reducing initial wait time
- Giving users control over which ideas to research
- Making the process more transparent and interactive

## Current Flow (Problematic)
```
Upload PDF → Analyze (all at once) → Wait 5-10 min → Get 3 results
```

## Proposed Flow (Better)
```
Upload PDF → Read Paper (1-2 min) → Review 10 ideas →
Select ideas → Search & Rank (2-4 min) → Get top 3 results
```

## Implementation Steps

### 1. API Changes

**Modify `/api/analyze` endpoint:**
- Make it only run Reader Agent
- Return the 10 raw ideas immediately
- Status changes: `uploaded → parsing → reading → ideas_ready`

**Add new `/api/search` endpoint:**
```python
POST /api/search
{
  "analysis_id": "uuid",
  "selected_idea_ids": [0, 2, 5, 7]  # Indices of ideas to research
}
```
- Takes analysis_id and selected idea indices
- Runs Searcher Agent only on selected ideas
- Status changes: `ideas_ready → searching → complete`

### 2. Database Schema Changes

**Update Analysis model:**
- Current status values: `pending, parsing, reading, searching, complete, error`
- Add new status: `ideas_ready` (between `reading` and `searching`)
- Reader output already stored in `reader_output` JSON field ✓
- No schema changes needed, just status flow changes

### 3. Backend Changes

**File: app.py**

**Update `/api/analyze` endpoint (line 119-246):**
- Remove Searcher Agent call
- Stop after Reader Agent completes
- Set status to `ideas_ready` instead of `searching`
- Return ideas immediately

**Add new `/api/search` endpoint:**
```python
@app.route('/api/search', methods=['POST'])
def search_ideas():
    """
    Search and rank selected research ideas
    Expects: analysis_id, selected_idea_ids (list of indices)
    """
    # Get analysis record
    # Get reader_output ideas
    # Filter to selected ideas only
    # Run Searcher Agent
    # Save top 3 results
    # Set status to 'complete'
```

**Update `/api/results` endpoint (line 272-302):**
- Allow retrieving results when status is `ideas_ready` (show ideas without scores)
- Only require `complete` status for full results with rankings

### 4. Frontend Changes

**File: index.html**

**Add new UI state: "Review Ideas"**

After Reader Agent completes, show:
```html
<!-- Ideas Review Section -->
<div id="ideas-review-section" class="hidden">
  <h2>Research Ideas Generated</h2>
  <p>Select ideas to research and rank (recommended: 3-5 ideas)</p>

  <!-- Idea cards with checkboxes -->
  <div class="space-y-16">
    <!-- For each idea -->
    <div class="idea-card">
      <input type="checkbox" checked />
      <h3>{idea.title}</h3>
      <p>{idea.description}</p>
      <p class="text-sm">{idea.rationale}</p>
    </div>
  </div>

  <button id="search-btn">Search & Rank Selected Ideas</button>
</div>
```

**Update JavaScript flow:**
1. After `/api/analyze` completes, fetch results
2. Display all 10 ideas with checkboxes (all checked by default)
3. User can uncheck ideas they don't want to research
4. Click "Search & Rank" → Call new `/api/search` endpoint
5. Poll for completion and show final ranked results

### 5. Progress Indicator Updates

**Two-stage progress:**
- Stage 1: Reading (0-50%)
  - Parsing PDF: 0-20%
  - Reading paper: 20-50%
- Stage 2: Searching (50-100%)
  - Searching literature: 50-80%
  - Ranking ideas: 80-100%

## Reasoning

**Benefits:**
1. **Faster feedback** - Users see ideas in 1-2 minutes instead of waiting 10 minutes
2. **User control** - Users can focus resources on most promising ideas
3. **Cost savings** - Don't waste API calls on ideas users aren't interested in
4. **Better UX** - Clear progress, no black box waiting
5. **Flexibility** - Users can research all 10 or just 2-3

**Minimal changes:**
- Database schema unchanged (just status flow)
- Most backend logic reusable
- Frontend gets one new section

## Tasks Breakdown

1. **Backend: Update `/api/analyze`** - Remove Searcher call, return after Reader
2. **Backend: Create `/api/search`** - New endpoint for selected ideas
3. **Backend: Update `/api/results`** - Handle `ideas_ready` status
4. **Frontend: Add ideas review UI** - Checkbox cards for idea selection
5. **Frontend: Update workflow** - Two-step process with new button
6. **Frontend: Update progress** - Two-stage progress indicator
7. **Testing: Verify full flow** - Upload → Review → Search → Results

## MVP Approach
- Keep it simple: All ideas checked by default
- Users can uncheck if they want
- Minimum 1 idea must be selected
- Maximum 10 ideas can be selected
