"""
Reader Agent
Analyzes research papers and generates follow-up research ideas
"""

import os
import json
import google.generativeai as genai


class ReaderAgent:
    def __init__(self):
        """Initialize Reader Agent with Gemini API"""
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze_paper(self, paper_text, topics):
        """
        Analyze paper and generate research ideas

        Args:
            paper_text: Full text of the research paper
            topics: List of user-selected topic strings

        Returns:
            Dictionary with paper analysis and generated ideas
        """
        # Step 1: Extract concepts and analyze paper
        extraction = self._extract_concepts(paper_text)

        # Step 2: Match user topics with paper content
        matched_user_topics = self._match_user_topics(paper_text, extraction, topics)

        # Step 3: Generate research ideas based on extraction and topics
        ideas = self._generate_ideas(paper_text, extraction, topics)

        return {
            'summary': extraction.get('summary', []),
            'methodology': extraction.get('methodology', []),
            'concepts': extraction.get('concepts', []),
            'matched_user_topics': matched_user_topics,
            'findings': extraction.get('findings', []),
            'limitations': extraction.get('limitations', []),
            'datasets': extraction.get('datasets', []),
            'future_work': extraction.get('future_work', []),
            'ideas': ideas
        }

    def _extract_concepts(self, paper_text):
        """
        Extract key concepts, findings, and other information from paper

        Returns:
            Dictionary with extracted information
        """
        prompt = f"""You are a research analyst. Analyze this research paper and extract key information.

Paper text:
{paper_text[:15000]}

Please extract and return the following in JSON format:
1. summary: Array of 3-4 bullet points summarizing the paper's key contributions (as array of strings)
2. methodology: Array of 2-4 bullet points describing the methods/techniques used (as array of strings)
3. concepts: List of EXACTLY 5-7 MOST IMPORTANT key concepts, ordered by importance (most important first)
   - The first concept should be the CORE/MAIN concept or methodology of the paper
   - Following concepts should be supporting concepts, techniques, or domains
   - Keep concepts concise (2-4 words each)
4. findings: List of 3-5 main findings or results (as strings)
5. limitations: List of limitations mentioned by authors (as strings)
6. datasets: List of datasets mentioned in the paper (as strings)
7. future_work: List of future work suggestions mentioned by authors (as strings)

Return ONLY valid JSON with these fields. Example format:
{{
  "summary": ["This paper presents a novel transformer architecture for NLP tasks", "Achieves state-of-the-art results on machine translation benchmarks", "Introduces self-attention mechanism to replace recurrent layers"],
  "methodology": ["Uses multi-head attention mechanism with 8 parallel attention layers", "Trained on WMT 2014 English-German dataset with 4.5M sentence pairs", "Applied layer normalization and residual connections"],
  "concepts": ["transformer architecture", "attention mechanism", "natural language processing", "self-attention", "encoder-decoder"],
  "findings": ["The model achieves...", ...],
  "limitations": ["Limited to...", ...],
  "datasets": ["ImageNet", ...],
  "future_work": ["Extending to...", ...]
}}"""

        try:
            response = self.model.generate_content(prompt)

            # Parse JSON from response
            content = response.text
            # Extract JSON from response (handle cases where Gemini adds explanation)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]

            extraction = json.loads(content)
            return extraction

        except Exception as e:
            print(f"Error in concept extraction: {e}")
            return {
                'summary': [],
                'methodology': [],
                'concepts': [],
                'findings': [],
                'limitations': [],
                'datasets': [],
                'future_work': []
            }

    def _match_user_topics(self, paper_text, extraction, topics):
        """
        Match user-selected topics with paper content to find relevant interests

        Args:
            paper_text: Full text of the research paper
            extraction: Extracted information from the paper
            topics: List of user-selected topic strings

        Returns:
            List of user topics that are relevant to the paper
        """
        if not topics:
            return []

        # Combine paper summary and concepts for matching context
        paper_context = " ".join(extraction.get('summary', []))
        paper_concepts = " ".join(extraction.get('concepts', []))
        combined_context = f"{paper_context} {paper_concepts}".lower()

        matched_topics = []

        for topic in topics:
            topic_lower = topic.lower()
            topic_words = topic_lower.split()

            # Check if topic or its words appear in paper context
            if topic_lower in combined_context:
                matched_topics.append(topic)
            elif any(word in combined_context for word in topic_words if len(word) > 3):
                matched_topics.append(topic)

        # Limit to top 5 matched topics
        return matched_topics[:5]

    def _generate_ideas(self, paper_text, extraction, topics):
        """
        Generate follow-up research ideas based on paper analysis

        Returns:
            List of idea dictionaries
        """
        topics_str = ", ".join(topics)

        prompt = f"""You are a research advisor helping generate novel research ideas based on a paper.

Paper Summary: {extraction.get('summary', '')}

Key Concepts: {', '.join(extraction.get('concepts', [])[:10])}

Main Findings: {', '.join(extraction.get('findings', []))}

Limitations: {', '.join(extraction.get('limitations', []))}

Future Work Suggested: {', '.join(extraction.get('future_work', []))}

User's Research Interests: {topics_str}

Generate 8-10 follow-up research ideas that could extend this work. Each idea should:
- Build on the paper's contributions
- Address limitations or explore new directions
- Align with user's topics of interest where possible
- Be specific and actionable

For each idea, provide:
1. title: A concise, descriptive title (5-10 words)
2. description: A 2-3 sentence description of the research idea
3. rationale: Why this is an interesting research direction (1-2 sentences)
4. topic_tags: List of relevant topics from user's interests that match this idea

Return ONLY valid JSON as an array of ideas. Example format:
[
  {{
    "title": "Applying Transformers to Time Series Forecasting",
    "description": "Extend the transformer architecture to multivariate time series prediction...",
    "rationale": "While transformers excel at sequence modeling...",
    "topic_tags": ["Machine Learning", "Time Series"]
  }},
  ...
]"""

        try:
            response = self.model.generate_content(prompt)

            # Parse JSON from response
            content = response.text
            # Extract JSON array from response
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                content = content[json_start:json_end]

            ideas = json.loads(content)

            # Ensure each idea has required fields
            for idea in ideas:
                if 'title' not in idea:
                    idea['title'] = 'Untitled Idea'
                if 'description' not in idea:
                    idea['description'] = ''
                if 'rationale' not in idea:
                    idea['rationale'] = ''
                if 'topic_tags' not in idea:
                    idea['topic_tags'] = []

            return ideas

        except Exception as e:
            print(f"Error in idea generation: {e}")
            return []
