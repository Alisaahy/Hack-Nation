"""
Google Scholar Scraper Utility
Extracts profile data from Google Scholar URLs
"""

import re
import time
from scholarly import scholarly
from urllib.parse import urlparse, parse_qs


def extract_user_id_from_url(scholar_url):
    """
    Extract user ID from Google Scholar URL
    
    Args:
        scholar_url: Google Scholar profile URL
            e.g., "https://scholar.google.com/citations?user=ABC123"
    
    Returns:
        User ID string, or None if not found
    """
    try:
        parsed = urlparse(scholar_url)
        query_params = parse_qs(parsed.query)
        
        if 'user' in query_params:
            return query_params['user'][0]
        return None
    except Exception as e:
        print(f"Error parsing URL: {e}")
        return None


def scrape_scholar_profile(scholar_url):
    """
    Scrape Google Scholar profile data
    
    Args:
        scholar_url: Google Scholar profile URL
    
    Returns:
        Dictionary with scholar profile data:
        {
            "name": str,
            "affiliation": str,
            "interests": [str],
            "publications": [{title, year, citations, venue}],
            "h_index": int,
            "total_citations": int
        }
    """
    try:
        # Extract user ID from URL
        user_id = extract_user_id_from_url(scholar_url)
        if not user_id:
            raise ValueError("Could not extract user ID from Google Scholar URL. Please ensure the URL contains 'user=' parameter.")
        
        # Search for author by ID
        # Add delay to avoid rate limiting
        time.sleep(1)
        
        # Try to get author using search_author_id
        # Note: search_author_id returns a dict directly, not an iterator
        try:
            author = scholarly.search_author_id(user_id)
            # Fill the author data to get complete information
            author = scholarly.fill(author)
        except Exception as e:
            raise ValueError(f"Could not find or load author with ID {user_id}. Error: {str(e)}. Please verify the Google Scholar URL is correct.")
        
        # Extract profile information
        name = author.get('name', 'Unknown')
        affiliation = author.get('affiliation', 'Unknown')
        
        # Extract interests
        interests = author.get('interests', [])
        
        # Extract citation metrics
        h_index = 0
        total_citations = 0
        
        # Try different possible keys for citation metrics
        if 'citedby' in author:
            total_citations = author['citedby']
        elif 'cited_by' in author:
            total_citations = author['cited_by']
        
        # Get h-index
        if 'hindex' in author:
            h_index = author['hindex']
        elif 'h_index' in author:
            h_index = author['h_index']
        elif 'indices' in author and 'h' in author['indices']:
            h_index = author['indices']['h']
        
        # Extract publications
        publications = []
        pub_list = author.get('publications', [])
        
        if pub_list:
            # Limit to top 15 publications to avoid timeout
            for pub in pub_list[:15]:
                try:
                    # Get basic info first (faster)
                    pub_data = {
                        'title': '',
                        'year': '',
                        'citations': 0,
                        'venue': '',
                        'authors': []
                    }
                    
                    # Try to get data from pub dict directly first
                    if 'bib' in pub:
                        bib = pub['bib']
                        pub_data['title'] = bib.get('title', 'Unknown Title')
                        pub_data['year'] = str(bib.get('pub_year', '')) if bib.get('pub_year') else ''
                        pub_data['venue'] = bib.get('venue', '')
                        pub_data['authors'] = bib.get('author', [])
                        if isinstance(pub_data['authors'], str):
                            pub_data['authors'] = [pub_data['authors']]
                    
                    pub_data['citations'] = pub.get('num_citations', 0) or pub.get('num_cited_by', 0) or 0
                    
                    # Only try to fill if we don't have title
                    if not pub_data['title'] or pub_data['title'] == 'Unknown Title':
                        try:
                            time.sleep(0.3)  # Small delay to avoid rate limiting
                            filled_pub = scholarly.fill(pub)
                            if 'bib' in filled_pub:
                                bib = filled_pub['bib']
                                pub_data['title'] = bib.get('title', 'Unknown Title')
                                pub_data['year'] = str(bib.get('pub_year', '')) if bib.get('pub_year') else ''
                                pub_data['venue'] = bib.get('venue', '')
                                pub_data['authors'] = bib.get('author', [])
                                if isinstance(pub_data['authors'], str):
                                    pub_data['authors'] = [pub_data['authors']]
                            pub_data['citations'] = filled_pub.get('num_citations', 0) or filled_pub.get('num_cited_by', 0) or 0
                        except Exception as fill_error:
                            # If fill fails, skip this publication
                            print(f"Warning: Could not fill publication details: {fill_error}")
                            continue
                    
                    # Only add if we have at least a title
                    if pub_data['title'] and pub_data['title'] != 'Unknown Title':
                        publications.append(pub_data)
                        
                except Exception as e:
                    # Skip publications that fail to load
                    print(f"Warning: Could not process publication: {e}")
                    continue
        
        # Ensure we have at least basic data
        if not name or name == 'Unknown':
            raise ValueError("Could not extract author name from Google Scholar profile")
        
        return {
            'name': name,
            'affiliation': affiliation,
            'interests': interests,
            'publications': publications,
            'h_index': h_index,
            'total_citations': total_citations
        }
        
    except ValueError:
        # Re-raise ValueError as-is (these are our custom errors)
        raise
    except Exception as e:
        print(f"Error scraping Google Scholar profile: {e}")
        import traceback
        traceback.print_exc()
        raise ValueError(f"Failed to scrape Google Scholar profile: {str(e)}. Please verify the URL is correct and try again.")

