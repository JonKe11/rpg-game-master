# backend/app/core/scraper/data_extractor.py
"""
Data Extractor - HTML parsing and data extraction from wiki pages.

Separates extraction logic from scraping orchestration (SRP).
Uses Beautiful Soup for HTML parsing.
"""

import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Extracts structured data from wiki HTML pages.
    
    Responsibilities:
    - Parse HTML with Beautiful Soup
    - Extract name, description, biography, etc.
    - Extract infobox data
    - Extract images
    """
    
    def __init__(self):
        pass
    
    def extract_all(self, html_content: str, url: str) -> Dict:
        """
        Extract all data from HTML page.
        
        Args:
            html_content: Raw HTML content
            url: Source URL (for logging)
            
        Returns:
            Dict with all extracted data
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            return {
                'name': self.extract_name(soup),
                'description': self.extract_description(soup),
                'biography': self.extract_biography(soup),
                'abilities': self.extract_abilities(soup),
                'affiliations': self.extract_affiliations(soup),
                'appearances': self.extract_appearances(soup),
                'image_url': self.extract_image(soup),
                'info_box': self.extract_infobox(soup)
            }
            
        except Exception as e:
            logger.error(f"Extraction failed for {url}: {e}")
            return {}
    
    def extract_name(self, soup: BeautifulSoup) -> str:
        """Extract page title/name."""
        # Try page header
        title_element = soup.find('h1', class_='page-header__title')
        if title_element:
            return title_element.text.strip()
        
        # Try title tag
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.text.split('|')[0].strip()
        
        return "Unknown"
    
    def extract_description(self, soup: BeautifulSoup) -> str:
        """Extract first paragraph (short description)."""
        content = soup.find('div', class_='mw-parser-output')
        if not content:
            return ""
        
        # Find first meaningful paragraph
        paragraphs = content.find_all('p', recursive=False)
        for p in paragraphs:
            text = p.text.strip()
            if text and len(text) > 20:
                # Remove citation markers [1], [2], etc.
                text = re.sub(r'\[\d+\]', '', text)
                return text
        
        return ""
    
    def extract_biography(self, soup: BeautifulSoup) -> str:
        """Extract biography/history sections."""
        biography_sections = []
        headers = soup.find_all(['h2', 'h3'])
        
        for header in headers:
            header_text = header.text.lower()
            
            # Look for Biography or History sections
            if 'biography' in header_text or 'history' in header_text:
                current = header.find_next_sibling()
                section_text = []
                
                # Collect paragraphs until next header
                while current and current.name not in ['h2', 'h3']:
                    if current.name == 'p':
                        text = current.text.strip()
                        text = re.sub(r'\[\d+\]', '', text)  # Remove citations
                        if text:
                            section_text.append(text)
                    current = current.find_next_sibling()
                
                if section_text:
                    biography_sections.append('\n'.join(section_text))
        
        # Limit to 2000 chars
        result = '\n\n'.join(biography_sections)
        return result[:2000] if result else ""
    
    def extract_abilities(self, soup: BeautifulSoup) -> List[str]:
        """Extract abilities/powers/skills lists."""
        abilities = []
        headers = soup.find_all(['h2', 'h3'])
        
        for header in headers:
            header_text = header.text.lower()
            
            # Look for ability-related sections
            if any(word in header_text for word in ['power', 'abilit', 'skill']):
                next_element = header.find_next_sibling()
                
                # Find list after header
                if next_element and next_element.name == 'ul':
                    for li in next_element.find_all('li'):
                        ability = li.text.strip()
                        ability = re.sub(r'\[\d+\]', '', ability)
                        if ability:
                            abilities.append(ability)
        
        # Limit to 10
        return abilities[:10]
    
    def extract_affiliations(self, soup: BeautifulSoup) -> List[str]:
        """Extract affiliations/organizations from infobox."""
        affiliations = []
        
        infobox = soup.find('aside', class_='portable-infobox')
        if not infobox:
            return affiliations
        
        # Look for Affiliation section in infobox
        sections = infobox.find_all('section')
        for section in sections:
            label = section.find('h3')
            if label and 'affiliation' in label.text.lower():
                # Get all links in this section
                values = section.find_all('a')
                for value in values:
                    affiliations.append(value.text.strip())
        
        # Unique values, max 5
        return list(set(affiliations))[:5]
    
    def extract_appearances(self, soup: BeautifulSoup) -> List[str]:
        """Extract list of appearances (media)."""
        appearances = []
        
        headers = soup.find_all('h2')
        for header in headers:
            if 'appearances' in header.text.lower():
                next_element = header.find_next_sibling()
                
                # Find list
                if next_element and next_element.name == 'ul':
                    for li in next_element.find_all('li')[:10]:  # Max 10
                        appearances.append(li.text.strip())
        
        return appearances
    
    def extract_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main image URL."""
        # Try infobox first
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            img = infobox.find('img')
            if img and 'src' in img.attrs:
                return img['src']
        
        # Try main content
        content = soup.find('div', class_='mw-parser-output')
        if content:
            img = content.find('img')
            if img and 'src' in img.attrs:
                return img['src']
        
        return None
    
    def extract_infobox(self, soup: BeautifulSoup) -> Dict:
        """Extract all key-value pairs from infobox."""
        info = {}
        
        infobox = soup.find('aside', class_='portable-infobox')
        if not infobox:
            return info
        
        # Extract all data items
        sections = infobox.find_all('div', class_='pi-item')
        for section in sections:
            label = section.find('h3', class_='pi-data-label')
            value = section.find('div', class_='pi-data-value')
            
            if label and value:
                key = label.text.strip().lower().replace(' ', '_')
                val = value.text.strip()
                info[key] = val
        
        return info