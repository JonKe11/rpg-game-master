# backend/app/services/biography_generator.py
from sqlalchemy.orm import Session
import ollama
import logging
from typing import Optional

from app.services.postgres_cache_service import PostgresCacheService
from app.services.scraper_service import ScraperService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

class BiographyGenerator:
    def __init__(self, db: Session):
        self.wiki_cache = PostgresCacheService(db)
        self.scraper = ScraperService()
        self.client = ollama.Client()
        self.model_name = get_settings().ollama_model

    async def _fetch_deep_context(self, term: str, universe: str, category: str) -> str:
        """
        Deep RAG Logic (Async):
        1. Check if term exists in DB (to catch correct canonical name).
        2. If yes -> fetch full data from web (Scraper) for that specific name.
        3. If not in DB -> try searching web directly.
        """
        if not term:
            return ""
            
        try:
           
            cached_article = self.wiki_cache.get_article_by_title(term, universe)
            
            search_term = term
            if cached_article:
           
                search_term = cached_article.title
                logger.info(f"📚 Found canonical term in DB: {search_term}")

  
            logger.info(f"🌍 Fetching LIVE deep context for: {search_term}...")
            
       
            if category == 'planets':
                data = await self.scraper.get_planet_info(search_term, universe)
            elif category == 'organizations':
                data = await self.scraper.get_affiliation_info(search_term, universe)
            else:
                data = await self.scraper.get_entity_data(search_term, universe)
                
      
            description = data.get('description', '')
            

            return description[:2000]
            
        except Exception as e:
            logger.warning(f"⚠️ Context fetch failed for {term}: {e}")
            return ""

    async def generate(self, name: str, race: str, profession: str, universe: str, homeworld: str = None, affiliation: str = None, age: int = None, gender: str = None, skin_color: str = None, eye_color: str = None) -> str:
        """
        Główna metoda generująca biografię (Async).
        """
        logger.info(f"🚀 Starting Deep Bio Generation for {name} ({race})")

      
        
   
        race_ctx = await self._fetch_deep_context(race, universe, 'species')
        class_ctx = await self._fetch_deep_context(profession, universe, 'classes')
        planet_ctx = await self._fetch_deep_context(homeworld, universe, 'planets')
        affil_ctx = await self._fetch_deep_context(affiliation, universe, 'organizations')

        knowledge_base = f"""
        SOURCE KNOWLEDGE (CANONICAL FACTS):
        - RACE ({race}): {race_ctx or "No detailed data."}
        - PROFESSION ({profession}): {class_ctx or "No detailed data."}
        - PLANET ({homeworld}): {planet_ctx or "No detailed data."}
        - FACTION ({affiliation}): {affil_ctx or "Operates independently."}
        """

     
        physical_desc = f"""
        - Age: {age if age else "Unknown"}
        - Gender: {gender if gender else "Unknown"}
        - Skin: {skin_color if skin_color else "Typical for race"}
        - Eyes: {eye_color if eye_color else "Typical for race"}
        """
        
        draft_prompt = f"""
        You are a professional Science-Fiction/Fantasy author (PG-13). 
        Your goal is to create a biography draft for a new character in the {universe} universe.

        CHARACTER DATA:
        Name: {name}
        Race: {race}
        Class: {profession}
        Origin: {homeworld if homeworld else "Undefined"}
        Faction: {affiliation if affiliation else "None"}

        {knowledge_base}

        🚨 SAFETY AND STYLE PROTOCOL:
        1. **SAFETY:** Content must be suitable for a PG-13 (Teen) audience. FORBIDDEN: erotica, extreme violence, profanity, hate speech.
        2. **UNIQUENESS:** Do not copy stories of famous heroes (e.g., Luke Skywalker). Create someone new.
        3. **LOGIC:** Use facts from the SOURCE KNOWLEDGE section. If the planet is a desert, the character cannot "swim in oceans".
        4. **LANGUAGE:** Avoid Earth-specific references (e.g., "Jesus", "Europe", "dollars"). Use English.

        TASK:
        Write a biography draft (approx. 150-200 words). Focus on motivation: why did {name} leave home and become a {profession}?
        """
        
        try:
            logger.info("✍️ Drafting biography...")
          
            draft_res = self.client.generate(
                model=self.model_name, 
                prompt=draft_prompt,
                options={'temperature': 0.7} 
            )
            draft_text = draft_res['response'].strip()
            

            
            polish_prompt = f"""
            You are the Editor-in-Chief of an RPG publisher.
            Polish the following character biography text to perfection.

            TEXT TO POLISH:
            "{draft_text}"

            EDITOR CHECKLIST:
            1. **Correctness:** Fix spelling, punctuation, and grammar errors.
            2. **Style:** The text must be serious, atmospheric, and fluid. Remove repetition and "fluff".
            3. **Consistency:** Ensure proper capitalization of proper nouns (e.g., "Twi'lek", not "twi'lek").
            4. **Safety Verification:** Ensure the text does not violate PG-13 rules (no profanity/erotica).
            5. **Language:** The output must be in English.

            Return ONLY the final, polished text.
            """
            
            logger.info("🧐 Polishing biography...")
            final_res = self.client.generate(
                model=self.model_name, 
                prompt=polish_prompt,
                options={'temperature': 0.3} 
            )
            return final_res['response'].strip()
            
        except Exception as e:
            logger.error(f"Bio Gen Error: {e}")
            return f"The chronicler system encountered an error: {str(e)}. Please try again."