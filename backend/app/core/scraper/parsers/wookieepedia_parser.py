# backend/app/core/scraper/parsers/wookieepedia_parser.py
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re
from .base_parser import BaseParser

class WookieepediaParser(BaseParser):
    """Single responsibility: parsowanie HTML Wookiepedii"""
    
    def parse_category_items(self, soup: BeautifulSoup) -> List[str]:
        """Wyciąga nazwy z kategorii"""
        items = []
        
        # Metoda 1: Nowa struktura Fandom
        members_div = soup.find('div', class_='category-page__members')
        if members_div:
            items = self._extract_from_new_structure(members_div)
        
        # Metoda 2: Stara struktura MediaWiki (fallback)
        if not items:
            category_div = soup.find('div', id='mw-pages')
            if category_div:
                items = self._extract_from_old_structure(category_div)
        
        return self._filter_valid_items(items)
    
    def parse_character_data(self, soup: BeautifulSoup) -> Dict:
        """Parsuje pełne dane postaci"""
        return {
            'name': self._parse_name(soup),
            'description': self._parse_description(soup),
            'biography': self._parse_biography(soup),
            'abilities': self._parse_abilities(soup),
            'image_url': self._parse_image(soup),
            'info': self._parse_infobox(soup),
            'affiliations': self._parse_affiliations(soup)
        }
    
    
    
    
    def find_next_page_url(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Znajduje link do następnej strony kategorii"""
        
        print(f"  🔍 Searching for next page link...")
        
        # Metoda 1: Nowa struktura Fandom
        next_link = soup.find('a', class_='category-page__pagination-next')
        if next_link and next_link.get('href'):
            href = next_link['href']
            url = base_url + href if href.startswith('/') else href
            print(f"  ✓ Found (method 1): {url}")
            return url
        
        # Metoda 2: MediaWiki standard
        next_link = soup.find('a', class_='mw-nextlink')
        if next_link and next_link.get('href'):
            href = next_link['href']
            url = base_url + href if href.startswith('/') else href
            print(f"  ✓ Found (method 2): {url}")
            return url
        
        # Metoda 3: Div paginacji
        pagination_div = soup.find('div', {'id': 'mw-pages'})
        if pagination_div:
            for link in pagination_div.find_all('a'):
                text = link.text.lower()
                if 'next' in text:
                    href = link.get('href')
                    if href:
                        url = base_url + href if href.startswith('/') else href
                        print(f"  ✓ Found (method 3): {url}")
                        return url
        
        # Metoda 4: Parametr pagefrom
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'pagefrom=' in href.lower():
                url = base_url + href if href.startswith('/') else href
                print(f"  ✓ Found (method 4): {url}")
                return url
        
        print(f"  ✗ No next page link found")
        return None
    
    def _extract_from_new_structure(self, div) -> List[str]:
        """Wyciąga z nowej struktury Fandom"""
        links = div.find_all('a', class_='category-page__member-link')
        return [link.get('title', link.text.strip()) for link in links if link.get('title') or link.text.strip()]
    
    def _extract_from_old_structure(self, div) -> List[str]:
        """Wyciąga ze starej struktury MediaWiki"""
        links = div.find_all('a')
        return [link.get('title', link.text.strip()) for link in links if link.get('title') or link.text.strip()]
    
    def _filter_valid_items(self, items: List[str]) -> List[str]:
        """Filtruj strony meta i niepotrzebne"""
        meta_prefixes = ['Category:', 'Template:', 'File:', 'Help:', 'User:', 'Talk:', 'Special:']
        return [
            item for item in items 
            if item and not any(item.startswith(prefix) for prefix in meta_prefixes)
        ]
    
    def _parse_name(self, soup: BeautifulSoup) -> str:
        """Nazwa postaci z nagłówka"""
        title_elem = soup.find('h1', class_='page-header__title')
        if title_elem:
            return title_elem.text.strip()
        
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.text.split('|')[0].strip()
        
        return "Unknown"
    
    def _parse_description(self, soup: BeautifulSoup) -> str:
        """Krótki opis - pierwszy paragraf"""
        content = soup.find('div', class_='mw-parser-output')
        if not content:
            return ""
        
        paragraphs = content.find_all('p', recursive=False)
        for p in paragraphs:
            text = p.text.strip()
            text = re.sub(r'\[\d+\]', '', text)  # Usuń przypisy [1], [2]
            if text and len(text) > 30:
                return text[:500]
        
        return ""
    
    def _parse_biography(self, soup: BeautifulSoup) -> str:
        """Biografia postaci z sekcji Biography/History"""
        bio_sections = []
        headers = soup.find_all(['h2', 'h3'])
        
        for header in headers:
            header_text = header.text.lower()
            if 'biography' in header_text or 'history' in header_text:
                current = header.find_next_sibling()
                section_text = []
                
                while current and current.name not in ['h2', 'h3']:
                    if current.name == 'p':
                        text = current.text.strip()
                        text = re.sub(r'\[\d+\]', '', text)
                        if text:
                            section_text.append(text)
                    current = current.find_next_sibling()
                
                if section_text:
                    bio_sections.append('\n'.join(section_text))
        
        return '\n\n'.join(bio_sections)[:3000]
    
    def _parse_abilities(self, soup: BeautifulSoup) -> List[str]:
        """Umiejętności i moce"""
        abilities = []
        headers = soup.find_all(['h2', 'h3'])
        
        for header in headers:
            header_text = header.text.lower()
            if any(word in header_text for word in ['power', 'abilit', 'skill', 'force']):
                next_elem = header.find_next_sibling()
                if next_elem and next_elem.name == 'ul':
                    for li in next_elem.find_all('li'):
                        ability = li.text.strip()
                        ability = re.sub(r'\[\d+\]', '', ability)
                        if ability:
                            abilities.append(ability)
        
        return abilities[:15]
    
    def _parse_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Główny obrazek z infoboxa"""
        infobox = soup.find('aside', class_='portable-infobox')
        if infobox:
            img = infobox.find('img', class_='pi-image-thumbnail')
            if img and img.get('src'):
                return img['src']
        
        return None
    
    def _parse_infobox(self, soup: BeautifulSoup) -> Dict:
        """Wszystkie dane z infoboxa"""
        info = {}
        infobox = soup.find('aside', class_='portable-infobox')
        
        if not infobox:
            return info
        
        for item in infobox.find_all('div', class_='pi-item'):
            label_elem = item.find('h3', class_='pi-data-label')
            value_elem = item.find('div', class_='pi-data-value')
            
            if not (label_elem and value_elem):
                continue
            
            key = label_elem.text.strip().lower()
            key = re.sub(r'[^\w\s]', '', key)
            key = key.replace(' ', '_')
            
            # Pobierz linki lub text
            links = value_elem.find_all('a')
            if links:
                value = ', '.join([link.text.strip() for link in links])
            else:
                value = value_elem.text.strip()
            
            value = re.sub(r'\[\d+\]', '', value)
            
            if value and value.lower() not in ['n/a', 'none', '']:
                info[key] = value
        
        return info
    
    def _parse_affiliations(self, soup: BeautifulSoup) -> List[str]:
        """Przynależności z infoboxa"""
        affiliations = set()
        infobox = soup.find('aside', class_='portable-infobox')
        
        if not infobox:
            return []
        
        for section in infobox.find_all('section'):
            label = section.find('h3', class_='pi-data-label')
            if label and 'affiliation' in label.text.lower():
                for link in section.find_all('a'):
                    aff = link.text.strip()
                    if aff and not aff.startswith('['):
                        affiliations.add(aff)
        
        return sorted(list(affiliations))[:10]