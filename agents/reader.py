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

        # Step 2: Generate research ideas based on extraction and topics
        ideas = self._generate_ideas(paper_text, extraction, topics)

        return {
            'summary': extraction.get('summary', ''),
            'concepts': extraction.get('concepts', []),
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
1. summary: A 3-4 sentence summary of the paper's key contributions
2. concepts: List of 10-15 key concepts, terms, or methodologies (as strings)
3. findings: List of 3-5 main findings or results (as strings)
4. limitations: List of limitations mentioned by authors (as strings)
5. datasets: List of datasets mentioned in the paper (as strings)
6. future_work: List of future work suggestions mentioned by authors (as strings)

Return ONLY valid JSON with these fields. Example format:
{{
  "summary": "This paper presents...",
  "concepts": ["neural networks", "attention mechanism", ...],
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
                'summary': '',
                'concepts': [],
                'findings': [],
                'limitations': [],
                'datasets': [],
                'future_work': []
            }

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
