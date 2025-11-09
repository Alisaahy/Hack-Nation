"""
Searcher Agent
Searches literature, assesses novelty/doability, and ranks research ideas
"""

import os
import json
import time
import requests
import xml.etree.ElementTree as ET
from urllib.parse import quote
import google.generativeai as genai


class SearcherAgent:
    def __init__(self):
        """Initialize Searcher Agent"""
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.arxiv_api = "http://export.arxiv.org/api/query"

    def research_ideas(self, ideas, user_topics):
        """
        Research each idea, assess novelty/doability, rank and return top 3

        Args:
            ideas: List of idea dictionaries from Reader Agent
            user_topics: List of user-selected topics

        Returns:
            Dictionary with top 3 ranked ideas with full details
        """
        scored_ideas = []

        # Process each idea
        for i, idea in enumerate(ideas):
            print(f"Processing idea {i+1}/{len(ideas)}: {idea['title']}")

            # Search for related papers
            papers = self._search_papers(idea)

            # Assess novelty
            novelty_assessment = self._assess_novelty(idea, papers)

            # Assess doability
            doability_assessment = self._assess_doability(idea, papers)

            # Calculate topic match score
            topic_match_score = self._calculate_topic_match(idea, user_topics)

            # Calculate composite score: 30% novelty + 40% doability + 30% topic match
            composite_score = (
                0.3 * novelty_assessment['novelty_score'] +
                0.4 * doability_assessment['doability_score'] +
                0.3 * topic_match_score
            )

            scored_ideas.append({
                'idea': idea,
                'papers': papers[:8],  # Keep top 8 papers
                'novelty_assessment': novelty_assessment,
                'doability_assessment': doability_assessment,
                'topic_match_score': topic_match_score,
                'composite_score': composite_score
            })

            # Rate limiting (Semantic Scholar: 100 req / 5 min)
            # Wait longer between ideas to avoid hitting rate limits
            time.sleep(3)

        # Sort by composite score
        scored_ideas.sort(key=lambda x: x['composite_score'], reverse=True)

        # Select top 3 with diversity check
        top_ideas = self._select_diverse_top_3(scored_ideas)

        # Synthesize literature for top 3
        for item in top_ideas:
            item['literature_synthesis'] = self._synthesize_literature(
                item['idea'],
                item['papers']
            )

        return {
            'top_ideas': top_ideas,
            'total_ideas_analyzed': len(ideas)
        }

    def _search_papers(self, idea, limit=20, max_retries=3):
        """
        Search for related papers using arXiv API

        Returns:
            List of paper dictionaries
        """
        # Construct search query from idea title and description
        search_terms = f"{idea['title']} {idea.get('description', '')[:100]}"

        # Clean and prepare query for arXiv
        query = quote(search_terms)

        for attempt in range(max_retries):
            try:
                # Query arXiv API
                url = f"{self.arxiv_api}?search_query=all:{query}&start=0&max_results={limit}&sortBy=relevance&sortOrder=descending"

                print(f"Searching arXiv for: {idea['title'][:50]}...")
                response = requests.get(url, timeout=15)
                response.raise_for_status()

                # Parse XML response
                root = ET.fromstring(response.content)

                # Define namespaces
                namespaces = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'arxiv': 'http://arxiv.org/schemas/atom'
                }

                # Extract papers
                formatted_papers = []
                entries = root.findall('atom:entry', namespaces)

                for entry in entries:
                    # Extract basic info
                    title = entry.find('atom:title', namespaces)
                    summary = entry.find('atom:summary', namespaces)
                    published = entry.find('atom:published', namespaces)
                    link = entry.find('atom:id', namespaces)

                    # Extract authors
                    authors = []
                    for author in entry.findall('atom:author', namespaces)[:3]:
                        name = author.find('atom:name', namespaces)
                        if name is not None:
                            authors.append(name.text)

                    # Only include if we have title and abstract
                    if title is not None and summary is not None:
                        # Extract year from published date (format: YYYY-MM-DD)
                        year = None
                        if published is not None:
                            try:
                                year = int(published.text[:4])
                            except:
                                year = None

                        formatted_papers.append({
                            'title': title.text.strip().replace('\n', ' '),
                            'abstract': summary.text.strip().replace('\n', ' ')[:500],  # Limit abstract length
                            'year': year,
                            'citations': 0,  # arXiv doesn't provide citation counts
                            'authors': authors,
                            'url': link.text if link is not None else ''
                        })

                print(f"Successfully fetched {len(formatted_papers)} papers from arXiv for: {idea['title'][:50]}")

                # arXiv requests a 3 second delay between requests
                time.sleep(3)

                return formatted_papers

            except requests.exceptions.RequestException as e:
                print(f"Error fetching from arXiv (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    wait_time = 3
                    print(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"Failed to fetch papers after {max_retries} attempts")
                    return []
            except Exception as e:
                print(f"Error parsing arXiv response: {e}")
                return []

        return []

    def _assess_novelty(self, idea, papers):
        """
        Use Claude to assess novelty of research idea

        Returns:
            Dictionary with novelty assessment
        """
        papers_summary = "\n\n".join([
            f"Title: {p['title']}\nYear: {p['year']}\nAbstract: {p['abstract'][:300]}..."
            for p in papers[:10]
        ])

        prompt = f"""Assess the novelty of this research idea based on existing literature.

Research Idea:
Title: {idea['title']}
Description: {idea['description']}

Related Papers Found:
{papers_summary}

Assess:
1. Has this specific idea been extensively explored? (Yes/Partially/No)
2. Research maturity level: Unexplored / Emerging / Active / Saturated
3. What specific gap or unexplored angle does this idea address?
4. Novelty score: Rate 1-5 (1=extensively explored, 5=highly novel)

Return ONLY valid JSON:
{{
  "explored": "Yes/Partially/No",
  "maturity": "Unexplored/Emerging/Active/Saturated",
  "gap": "description of gap",
  "novelty_score": 1-5
}}"""

        try:
            response = self.model.generate_content(prompt)

            content = response.text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]

            assessment = json.loads(content)
            return assessment

        except Exception as e:
            print(f"Error assessing novelty: {e}")
            return {
                'explored': 'Unknown',
                'maturity': 'Unknown',
                'gap': 'Unable to assess',
                'novelty_score': 3
            }

    def _assess_doability(self, idea, papers):
        """
        Use Gemini to assess doability/feasibility of research idea

        Returns:
            Dictionary with doability assessment
        """
        # Include paper info if available
        papers_context = ""
        if papers and len(papers) > 0:
            papers_context = f"\n\nRelated Research Papers:\n"
            for i, paper in enumerate(papers[:3]):
                papers_context += f"{i+1}. {paper['title']} ({paper['year']})\n"
            papers_context += "\nConsider these papers when assessing methodology and resources."

        prompt = f"""Assess the feasibility and doability of this research idea.

Research Idea:
Title: {idea['title']}
Description: {idea['description']}{papers_context}

Based on the idea and typical research resources, assess:
1. Data availability: Are datasets available or need to be collected? (Available/Partially/Need to Collect)
2. Methodology complexity: Can standard methods be used? (Standard/Moderate/Novel Methods Needed)
3. Estimated timeline: (3 months / 6 months / 1 year+)
4. Required expertise: (Undergraduate / Masters / PhD level)
5. Doability score: Rate 1-5 (1=very difficult, 5=highly doable)
   - Consider: data availability, methodology complexity, timeline, and expertise needed
   - Give VARIED scores (not all 3) - differentiate based on the specific challenges of THIS idea

Return ONLY valid JSON:
{{
  "data_availability": "Available/Partially/Need to Collect",
  "methodology": "Standard/Moderate/Novel Methods Needed",
  "timeline": "3 months/6 months/1 year+",
  "expertise_level": "Undergraduate/Masters/PhD level",
  "doability_score": 1-5
}}"""

        try:
            response = self.model.generate_content(prompt)

            content = response.text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]

            assessment = json.loads(content)
            print(f"Doability assessment for '{idea['title']}': {assessment.get('doability_score', 'N/A')}")
            return assessment

        except Exception as e:
            print(f"Error assessing doability: {e}")
            return {
                'data_availability': 'Unknown',
                'methodology': 'Unknown',
                'timeline': 'Unknown',
                'expertise_level': 'Unknown',
                'doability_score': 3
            }

    def _calculate_topic_match(self, idea, user_topics):
        """
        Calculate how well idea matches user's selected topics
        Uses semantic matching of idea content with user topics

        Returns:
            Score from 0-5
        """
        if not user_topics:
            return 3  # Neutral score if no topics

        # Combine idea title and description for matching
        idea_text = f"{idea.get('title', '')} {idea.get('description', '')}".lower()
        user_topics_lower = [topic.lower() for topic in user_topics]

        # Count how many user topics appear in the idea text
        matches = 0
        for topic in user_topics_lower:
            # Split topic into keywords for better matching
            topic_words = topic.split()
            # Check if any word from the topic appears in the idea
            if any(word in idea_text for word in topic_words if len(word) > 3):
                matches += 1

        # Score based on match ratio (0 to 5 scale)
        if not user_topics_lower:
            return 2.5

        match_ratio = matches / len(user_topics_lower)

        # Convert to 1-5 scale with variation
        # 0 matches = 1.5, all matches = 5.0
        score = 1.5 + (match_ratio * 3.5)

        print(f"Topic match for '{idea.get('title', 'N/A')}': {matches}/{len(user_topics_lower)} topics matched, score={score:.1f}")

        return round(score, 1)

    def _select_diverse_top_3(self, scored_ideas):
        """
        Select top 3 ideas ensuring diversity (not all similar)

        Returns:
            List of top 3 idea dictionaries
        """
        if len(scored_ideas) <= 3:
            return scored_ideas

        # Simple diversity check: take top idea, then find next ideas with different keywords
        top_3 = [scored_ideas[0]]

        for item in scored_ideas[1:]:
            if len(top_3) >= 3:
                break

            # Check if idea is different enough from already selected
            is_diverse = True
            current_title = item['idea']['title'].lower()

            for selected in top_3:
                selected_title = selected['idea']['title'].lower()
                # Simple diversity check: ensure titles don't share too many words
                current_words = set(current_title.split())
                selected_words = set(selected_title.split())
                common_words = current_words & selected_words
                if len(common_words) > 3:  # More than 3 common words
                    is_diverse = False
                    break

            if is_diverse:
                top_3.append(item)

        # If we didn't get 3 diverse ideas, just take top 3 by score
        if len(top_3) < 3:
            top_3 = scored_ideas[:3]

        return top_3

    def _synthesize_literature(self, idea, papers):
        """
        Synthesize literature for an idea

        Returns:
            Dictionary with synthesized literature information
        """
        papers_text = "\n\n".join([
            f"[{i+1}] {p['title']} ({p['year']})\n{p['abstract'][:200]}..."
            for i, p in enumerate(papers[:8])
        ])

        prompt = f"""Synthesize the literature for this research idea.

Research Idea: {idea['title']}

Related Papers:
{papers_text}

Create a synthesis that includes:
1. A brief overview of what has been done (2-3 sentences)
2. Key papers categorized as: Foundational Work, Recent Advances, or Identifies Gaps
3. What's missing or unexplored
4. Suggested approach (methodology, potential datasets, concrete next steps)

Return ONLY valid JSON:
{{
  "overview": "What has been done...",
  "key_papers": [
    {{"paper_index": 1, "category": "Foundational/Recent/Gap", "summary": "2 sentence summary"}},
    ...
  ],
  "whats_missing": "The specific gap...",
  "suggested_approach": "Concrete next steps..."
}}"""

        try:
            response = self.model.generate_content(prompt)

            content = response.text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]

            synthesis = json.loads(content)
            return synthesis

        except Exception as e:
            print(f"Error synthesizing literature: {e}")
            return {
                'overview': 'Unable to synthesize',
                'key_papers': [],
                'whats_missing': 'Unable to assess',
                'suggested_approach': 'Unable to provide'
            }
