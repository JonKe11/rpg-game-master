# backend/app/services/story_aware_game_master.py
"""
Game Master ze świadomością story arc
Wie w którym momencie kampanii jesteśmy i dostosowuje narrację
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging
import re

from app.services.campaign_planner import CampaignPlanner
from app.services.campaign_structure import CampaignArc, BeatType
from app.core.ai.adaptive_game_master import AdaptiveGameMaster
from app.services.session_storage import SessionStorage
# ⛔️ USUNIĘTO: from app.services.wiki_fetcher_service import WikiFetcherService
from app.core.ai.canon_validator import CanonValidator
from app.services.world_state import WorldState

# ✅ NOWE IMPORTY
from app.models.database import SessionLocal
from app.services.postgres_cache_service import PostgresCacheService
from app.models.wiki_article import WikiArticle # Potrzebne do typowania

logger = logging.getLogger(__name__)

# ========================================================================
# 🆕 NOWA: Funkcja pomocnicza do konwersji
# ========================================================================
def article_to_dict(article: WikiArticle) -> Dict:
    """Konwertuje obiekt WikiArticle SQLAlchemy na słownik dla AI."""
    if not article:
        return {}
    
    data = {
        'id': article.id,
        'name': article.title,
        'title': article.title,
        'description': article.content.get('description') if article.content else None,
        'abstract': article.content.get('abstract') if article.content else None,
        'image_url': article.image_url,
        'url': article.source_url,
        'source_url': article.source_url,
        'is_canon': True,
        'info_box': article.content or {} # Przekaż cały content jako info_box
    }
    
    # Dodaj 'structured' jeśli istnieje (dla lokacji)
    structured_data = {}
    if article.content:
        # Używamy kluczy parsowanych przez startup_prefetch_service
        if article.content.get('Region'): structured_data['region'] = article.content['Region']
        if article.content.get('System'): structured_data['system'] = article.content['System']
        # Stolica może być w content, ale nie jest parsowana automatycznie - AI może ją znaleźć w info_box
        if article.content.get('capital'): structured_data['capital'] = article.content['capital']
        if article.content.get('Capital'): structured_data['capital'] = article.content['Capital']
            
    if structured_data:
        data['structured'] = structured_data
        
    return data

class StoryAwareGameMaster:
    """
    Enhanced GM z:
    - Story arc tracking
    - RAG (wiki knowledge z PostgreSQL)
    - Campaign planning
    - Canon validation
    - World State management
    - Checkpoint validation
    """
    
    def __init__(
        self, 
        game_master: AdaptiveGameMaster,
        storage: SessionStorage
    ):
        self.gm = game_master
        self.storage = storage
        self.campaign_planner = CampaignPlanner(game_master)
        # ⛔️ USUNIĘTO: self.wiki_fetcher = WikiFetcherService()
        self.validator = None  # Lazy init per universe
        
        # ✅ NOWA LOGIKA: Dostęp do bazy danych PostgreSQL
        try:
            self.db = SessionLocal()
            self.pg_cache = PostgresCacheService(self.db)
            logger.info("✅ StoryAwareGameMaster połączony z PostgresCacheService")
        except Exception as e:
            logger.error(f"❌ StoryAwareGameMaster nie mógł połączyć się z DB: {e}")
            self.db = None
            self.pg_cache = None
    
    def __del__(self):
        """Zamknij sesję bazy danych, gdy serwis jest niszczony"""
        if self.db:
            self.db.close()
            
    def _get_validator(self, universe: str) -> CanonValidator:
        """Get validator for universe (lazy init)"""
        if self.validator is None or self.validator.universe != universe:
            logger.info(f"🔧 Initializing Canon Validator for {universe}...")
            self.validator = CanonValidator(universe)
        return self.validator
    
    def start_campaign(
        self, 
        session_id: int,
        character_data: Dict,
        universe: str,
        campaign_length: str = "medium"
    ) -> Dict:
        """Start campaign with World State and dynamic wiki-based validation"""
        
        existing_intro = self.storage.get_intro(session_id)
        if existing_intro:
            logger.warning(f"⚠️ Intro already exists for session {session_id} - returning cached")
            campaign = self.storage.get_campaign(session_id)
            world_state = self.storage.get_world_state(session_id)
            
            if campaign and world_state:
                current_beat = campaign.get_current_beat()
                return {
                    'message': existing_intro['message'],
                    'type': 'narration',
                    'location': existing_intro.get('location', world_state.current_planet),
                    'timestamp': existing_intro.get('timestamp', datetime.now().isoformat()),
                    'campaign': {
                        'title': campaign.title,
                        'theme': campaign.main_theme,
                        'progress': 0,
                        'current_beat': current_beat.title if current_beat else None,
                        'estimated_turns': campaign.total_estimated_turns
                    }
                }
        
        logger.info(f"📖 Starting NEW campaign for {character_data['name']}...")
        
        if not self.pg_cache:
             raise Exception("PostgresCacheService (pg_cache) is not available.")

        validator = self._get_validator(universe)
        
        # 1. Walidacja danych postaci
        if character_data.get('race'):
            if not validator.validate_species(character_data['race']):
                logger.warning(f"⚠️ Invalid species: {character_data['race']}")
                character_data['race'] = validator.get_fallback_species()
                logger.info(f"   → Using: {character_data['race']}")
        
        homeworld = character_data.get('homeworld')
        if homeworld and not validator.validate_planet(homeworld):
            logger.warning(f"⚠️ Invalid planet: {homeworld}")
            homeworld = validator.get_fallback_planet()
            logger.info(f"   → Using: {homeworld}")
        
        if not homeworld:
            homeworld = validator.get_fallback_planet()
        
        # 1b. POBIERZ KONTEKST Z POSTGRESQL
        location_article = self.pg_cache.get_article_by_title(homeworld, universe)
        
        capital_city = None
        location_content = {}
        location_context = {} # Słownik do przekazania
        
        if location_article:
            location_content = location_article.content or {}
            # Używamy danych sparsowanych przez startup_prefetch_service
            capital_city = location_content.get('Capital') or location_content.get('capital')
            # Konwertuj na dict dla _build_rich_wiki_context
            location_context = article_to_dict(location_article)
        
        if capital_city:
            logger.info(f"🏛️ Capital city: {capital_city}")
        else:
            logger.info(f"🏛️ Capital city: Not specified in wiki (AI can choose location freely)")
        
        # 1c. STWÓRZ WORLD STATE
        world_state = WorldState(
            universe=universe,
            starting_planet=homeworld,
            capital_city=capital_city,
            homeworld=homeworld
        )
        self.storage.save_world_state(session_id, world_state)
        logger.info(f"💾 World State created and saved")
        
        # 2. Generuj kampanię
        logger.info(f"📖 Planning {campaign_length} campaign...")
        campaign = self.campaign_planner.generate_campaign(
            character_data,
            universe,
            campaign_length
        )
        
        # 3. Zapisz kampanię
        self.storage.save_campaign(session_id, campaign)
        logger.info(f"✅ Campaign: '{campaign.title}'")
        
        current_beat = campaign.get_current_beat()
        
        # 4. Pobierz kontekst rasy
        race_wiki = None
        if character_data.get('race'):
            race_article = self.pg_cache.get_article_by_title(character_data['race'], universe)
            if race_article:
                race_wiki = article_to_dict(race_article)
        
        # 5. Zbuduj BOGATY kontekst
        wiki_data_with_structure = {}
        if race_wiki:
            wiki_data_with_structure[character_data['race']] = race_wiki
        
        if location_context:
            wiki_data_with_structure[homeworld] = {
                **location_context,
                'structured': location_context.get('structured', {})
            }
        
        wiki_context = self._build_rich_wiki_context(wiki_data_with_structure)
        world_context = world_state.get_world_context_for_prompt()
        
        # 6. Generuj intro
        intro_prompt = f"""You are Game Master for {universe} RPG.
{world_context}
CHARACTER:
- Name: {character_data['name']}
- Species: {character_data.get('race', 'Human')}
- Homeworld (origin): {homeworld} [for backstory only]
CAMPAIGN:
- Title: {campaign.title}
- Theme: {campaign.main_theme}
RICH WIKI CONTEXT (use this knowledge):
{wiki_context}
YOUR TASK:
Choose a starting location for the story:
1. Can be {homeworld} (character's homeworld) OR any other canon planet
2. If wiki shows a capital city, you may start there OR elsewhere on the planet
3. If no specific cities mentioned, create a vivid location
CREATIVE FREEDOM:
- Use wiki data as foundation
- Create specific unnamed locations within canon places
- If character not on homeworld, briefly mention why
LANGUAGE: English only
FORMAT: 2-3 sentence immersive intro
Write the intro:"""
        
        logger.info("🎨 Generating intro with AI...")
        intro_text = self.gm._generate_llm_response(intro_prompt, "")
        
        # 7. Walidacja i przetwarzanie
        actual_starting_planet = self._extract_planet_from_text(intro_text, validator, homeworld)
        if actual_starting_planet and actual_starting_planet != homeworld:
            logger.info(f"🌍 AI chose starting planet: {actual_starting_planet} (homeworld: {homeworld})")
            world_state.starting_planet = actual_starting_planet
            world_state.current_planet = actual_starting_planet
            
            # ✅ Pobierz dane nowej planety
            actual_location_article = self.pg_cache.get_article_by_title(actual_starting_planet, universe)
            if actual_location_article and actual_location_article.content:
                actual_capital = actual_location_article.content.get('capital') or actual_location_article.content.get('Capital')
                if actual_capital:
                    world_state.capital_city = actual_capital
                    logger.info(f"🏛️ Updated capital for {actual_starting_planet}: {world_state.capital_city}")
        else:
            logger.info(f"🌍 Starting on homeworld: {homeworld}")
        
        validation = validator.scan_and_validate(intro_text)
        serious_violations = [v for v in validation['invalid'] if len(v) > 6]
        
        if serious_violations:
            logger.warning(f"⚠️ SERIOUS VIOLATIONS detected: {serious_violations}")
            logger.info("🔄 Regenerating with ultra-safe fallback...")
            intro_text = self._generate_safe_intro(character_data, world_state.current_planet, campaign)
        else:
            logger.info(f"✅ Intro validated - no serious violations!")
        
        fact_check = self._fact_check_response(intro_text, universe, validator, wiki_data_with_structure)
        
        if not fact_check['valid']:
            logger.warning(f"🚨 FACT-CHECK FAILED: {fact_check['errors']}")
            logger.info("🔄 Regenerating with corrections...")
            intro_text = self._generate_safe_intro(character_data, world_state.current_planet, campaign)
        else:
            logger.info("✅ Fact-check passed!")
        
        checkpoint = self._validate_response_consistency(intro_text, world_state, validator)
        
        if not checkpoint['valid']:
            logger.warning(f"🚨 CHECKPOINT FAILED: {checkpoint['violations']}")
            if checkpoint['severity'] == 'critical':
                logger.info("🔄 Critical issue - regenerating...")
                intro_text = self._generate_safe_intro(character_data, world_state.current_planet, campaign)
            else:
                logger.info("🔧 Attempting auto-fix...")
                intro_text = self._fix_response(intro_text, world_state, validator)
        else:
            logger.info("✅ Checkpoint passed!")
        
        world_state.add_event(f"Campaign '{campaign.title}' started on {world_state.current_planet}", turn=0)
        self._extract_and_add_npcs_from_text(intro_text, world_state, validator, turn=0)
        self.storage.save_world_state(session_id, world_state)
        
        # 8. Zapisz intro
        intro_data = {
            'message': intro_text, 'type': 'narration',
            'location': world_state.current_planet, 'timestamp': datetime.now().isoformat(),
            'validated': True, 'validation_result': validation
        }
        self.storage.save_intro(session_id, intro_data)
        logger.info(f"💾 Intro saved for session {session_id}")
        
        return {
            'message': intro_text, 'type': 'narration',
            'location': world_state.current_planet, 'timestamp': datetime.now().isoformat(),
            'campaign': {
                'title': campaign.title, 'theme': campaign.main_theme, 'progress': 0,
                'current_beat': current_beat.title if current_beat else None,
                'estimated_turns': campaign.total_estimated_turns
            }
        }
        
    def _generate_safe_intro(self, character_data: Dict, planet: str, campaign) -> str:
        """Ultra-safe intro when validation fails - uses only verified elements"""
        safe_intros = {
            'Tatooine': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} who has arrived on the desert world of Tatooine. The twin suns beat down mercilessly as you step into the dusty streets of Mos Eisley, where spacers and smugglers conduct their shadowy business.",
            'Coruscant': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} navigating the endless cityscape of Coruscant. Towering skyscrapers stretch into the polluted sky as speeders zip past overhead. Your journey begins in the bustling lower levels.",
            'Nar Shaddaa': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} who has come to Nar Shaddaa, the moon known as the Smuggler's Moon. Neon lights flicker in the perpetual twilight as you walk through crowded streets filled with criminals and outcasts from across the galaxy.",
            'default': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} beginning your journey on {planet}. The adventure ahead will test your skills and resolve."
        }
        return safe_intros.get(planet, safe_intros['default'])
    
    def process_action_with_story(
        self,
        session_id: int,
        action: str
    ) -> Dict:
        """Process action with World State tracking and story arc awareness"""
        
        if not self.pg_cache:
             raise Exception("PostgresCacheService (pg_cache) is not available.")
            
        campaign = self.storage.get_campaign(session_id)
        if not campaign: return {'error': 'Campaign not found'}
        
        world_state = self.storage.get_world_state(session_id)
        if not world_state:
            logger.warning(f"⚠️ World state not found for {session_id} - creating new one")
            world_state = WorldState(universe=campaign.universe, starting_planet="Tatooine", capital_city=None)
            self.storage.save_world_state(session_id, world_state)
        
        validator = self._get_validator(campaign.universe)
        current_beat = campaign.get_current_beat()
        current_turn = campaign.current_turn
        
        entities = self._extract_entities(action)
        
        # ✅ POBIERZ DANE Z POSTGRESQL
        wiki_data = {}
        for entity in entities[:2]:
            article = self.pg_cache.get_article_by_title(entity, campaign.universe)
            if article:
                wiki_data[entity] = article_to_dict(article)
        
        wiki_context = self._build_rich_wiki_context(wiki_data)
        world_context = world_state.get_world_context_for_prompt()
        
        prompt = f"""You are Game Master. Player action: "{action}"
{world_context}
CAMPAIGN STATUS:
- Title: {campaign.title}
- Turn: {current_turn}/{campaign.total_estimated_turns}
- Act: {campaign.current_act}
- Current Beat: {current_beat.title if current_beat else 'Unknown'}
- Beat Goal: {current_beat.description if current_beat else 'Continue'}
WIKI KNOWLEDGE (use as reference):
{wiki_context}
GUIDELINES:
1. Stay consistent with World State
2. Use wiki data to inform your descriptions
3. Create specific locations within canon places if needed
4. Push story toward beat goal
LANGUAGE: English only
FORMAT: 2-4 sentence natural narrative
Response:"""
        
        response_text = self.gm._generate_llm_response(prompt, "")
        
        # Walidacja
        validation = validator.scan_and_validate(response_text)
        if validation['invalid']: logger.warning(f"⚠️ Violations: {validation['invalid']}")
        
        fact_check = self._fact_check_response(response_text, campaign.universe, validator, wiki_data)
        if not fact_check['valid']: logger.warning(f"🚨 FACT-CHECK FAILED: {fact_check['errors']}")
        
        checkpoint = self._validate_response_consistency(response_text, world_state, validator)
        if not checkpoint['valid']:
             logger.warning(f"🚨 CHECKPOINT FAILED: {checkpoint['violations']}")
             if checkpoint['severity'] == 'critical':
                # Potrzebujemy character_data, którego tu nie mamy...
                # Użyjemy uproszczonego _generate_safe_intro
                response_text = f"You continue your journey on {world_state.current_planet}."
             else:
                response_text = self._fix_response(response_text, world_state, validator)
        
        world_state.add_event(f"Player: {action[:50]}...", turn=current_turn)
        self._extract_and_add_npcs_from_text(response_text, world_state, validator, turn=current_turn)
        
        if current_beat:
            current_beat.actual_turns_taken += 1
            if self._should_advance_beat(current_beat, action, response_text):
                logger.info(f"📖 Beat completed: {current_beat.title}")
                campaign.advance_beat()
                world_state.add_memory_trace(f"Story beat completed: {current_beat.title}", turn=current_turn, is_critical=True)
                next_beat = campaign.get_current_beat()
                if next_beat:
                    hint = self._get_story_hint(next_beat.beat_type)
                    if hint: response_text += f"\n\n*{hint}*"
        
        campaign.current_turn += 1
        campaign.last_updated = datetime.now()
        self.storage.save_campaign(session_id, campaign)
        self.storage.save_world_state(session_id, world_state)
        
        return {
            'message': response_text,
            'type': 'narration',
            'turn': campaign.current_turn,
            'timestamp': datetime.now().isoformat(),
            'campaign_progress': {
                'progress_percent': round(campaign.get_progress_percentage(), 1),
                'current_beat': current_beat.title if current_beat else None,
                'act': campaign.current_act,
                'turns_taken': campaign.current_turn,
                'total_turns': campaign.total_estimated_turns,
                'near_end': campaign.is_near_end(),
                'completed': campaign.is_completed()
            }
        }
    
    def _build_rich_wiki_context(self, wiki_data: Dict) -> str:
        """
        Build RICH context from wiki - structured and detailed
        """
        if not wiki_data:
            return "No wiki data available. Use your knowledge of the universe."
        
        parts = []
        for title, article in wiki_data.items():
            if not article: continue
            if not article.get('is_canon', True): continue
            
            context_block = f"\n{'='*60}\n📖 ARTICLE: {title}\n{'='*60}\n"
            if article.get('description'):
                context_block += f"\nDESCRIPTION:\n{article['description'][:400]}\n"
            
            if 'structured' in article:
                struct = article['structured']
                context_block += f"\nSTRUCTURED INFO:\n"
                if struct.get('region'): context_block += f"- Region: {struct['region']}\n"
                if struct.get('system'): context_block += f"- System: {struct['system']}\n"
                if struct.get('capital'): context_block += f"- Capital: {struct['capital']}\n"
            
            if article.get('info_box') and isinstance(article['info_box'], dict):
                relevant_keys = ['population', 'government', 'species', 'language', 'terrain']
                info_items = []
                for key, value in article['info_box'].items():
                    key_lower = key.lower()
                    if any(rk in key_lower for rk in relevant_keys):
                        if key_lower not in ['region', 'system', 'capital', 'description']:
                            info_items.append(f"{key}: {value}")
                
                if info_items:
                    context_block += f"\nADDITIONAL INFO:\n"
                    for item in info_items[:5]:
                        context_block += f"- {item}\n"
            
            parts.append(context_block)
        
        return "\n".join(parts) if parts else "No detailed wiki data. Use general universe knowledge."
    
    def _fact_check_response(
        self,
        text: str,
        universe: str,
        validator,
        wiki_context_data: Dict = None
    ) -> Dict[str, any]:
        """Fact-check response using ACTUAL WIKI DATA"""
        errors = []
        corrections = {}
        
        if not wiki_context_data:
            return {'valid': True, 'errors': [], 'corrections': {}}
        
        for title, article in wiki_context_data.items():
            if not article: continue
            struct = article.get('structured', {})
            location_name = title.lower()
            
            if location_name in text.lower():
                if struct.get('type') == 'moon':
                    wrong_phrases = [f'{title.lower()}.*planet', f'planet.*{title.lower()}']
                    for phrase in wrong_phrases:
                        if re.search(phrase, text.lower()):
                            errors.append(f"{title} is a moon, not a planet")
                
                if struct.get('capital'):
                    wiki_capital = struct['capital'].lower()
                    capital_pattern = f'{location_name}.*capital.*?([A-Z][a-z]+)'
                    matches = re.findall(capital_pattern, text, re.IGNORECASE)
                    for mentioned_capital in matches:
                        if mentioned_capital.lower() != wiki_capital and mentioned_capital.lower() != title.lower():
                            errors.append(f"Wiki says capital of {title} is {struct['capital']}, not {mentioned_capital}")
                            corrections[mentioned_capital] = struct['capital']
        
        return {'valid': len(errors) == 0, 'errors': errors, 'corrections': corrections}
    
    def _validate_response_consistency(
        self,
        response: str,
        world_state: WorldState,
        validator
    ) -> Dict[str, any]:
        """Checkpoint validation - sprawdź czy AI nie namieszał"""
        violations = []
        severity = 'none'  # none, minor, major, critical
        
        if world_state.current_planet:
            other_planets = validator.get_canon_planets(limit=100)
            wrong_planets_mentioned = []
            for planet in other_planets:
                if planet == world_state.current_planet: continue
                if planet.lower() in response.lower():
                    wrong_planets_mentioned.append(planet)
            if wrong_planets_mentioned:
                violations.append(f"Mentioned wrong planet(s): {wrong_planets_mentioned}")
                severity = 'critical'
        
        for npc_name, npc_data in world_state.npcs.items():
            if npc_name in response:
                correct_race = npc_data.race
                other_races = validator.get_canon_species(limit=50)
                for race in other_races:
                    if race != correct_race and race.lower() in response.lower():
                        pattern = f"{npc_name}.{{0,50}}{race}|{race}.{{0,50}}{npc_name}"
                        if re.search(pattern, response, re.IGNORECASE):
                            violations.append(f"Changed {npc_name}'s race from {correct_race} to {race}")
                            severity = 'major'
        
        metadata_keywords = ['world state', 'established facts', 'memory traces', 'turn 0:', 'current location:']
        for keyword in metadata_keywords:
            if keyword.lower() in response.lower():
                violations.append(f"Leaked metadata: '{keyword}'")
                severity = 'minor'
        
        polish_indicators = ['ą', 'ę', 'ć', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
        if any(char in response for char in polish_indicators):
            violations.append("Response contains non-English text (Polish detected)")
            severity = 'major'
        
        return {'valid': len(violations) == 0 or severity == 'minor', 'violations': violations, 'severity': severity}
        
    def _fix_response(
        self,
        response: str,
        world_state: WorldState,
        validator
    ) -> str:
        """Auto-fix common mistakes in response"""
        fixed = response
        if world_state.current_planet:
            wrong_planets = validator.get_canon_planets(limit=100)
            for wrong_planet in wrong_planets:
                if wrong_planet != world_state.current_planet:
                    pattern = re.compile(re.escape(wrong_planet), re.IGNORECASE)
                    fixed = pattern.sub(world_state.current_planet, fixed)
        
        fixed = re.sub(r'\n- (Miejsce|Data|Godzina|Turn|Beat):.*', '', fixed, flags=re.IGNORECASE)
        fixed = re.sub(r'\n{3,}', '\n\n', fixed)
        fixed = fixed.strip()
        return fixed
    
    def _should_regenerate(
        self,
        validation_result: Dict,
        response: str
    ) -> bool:
        """Decide if response should be regenerated"""
        severity = validation_result['severity']
        if severity == 'critical': return True
        if severity == 'major':
            if len(response.strip()) < 50: return True
            if any('Polish' in v or 'non-English' in v for v in validation_result['violations']): return True
            return False
        return False
    
    def _should_advance_beat(self, beat, action: str, response: str) -> bool:
        """Decide if beat should advance"""
        if beat.actual_turns_taken < max(3, beat.estimated_turns - 2): return False
        if beat.actual_turns_taken >= beat.estimated_turns + 3: return True
        if beat.trigger_keyword:
            if beat.trigger_keyword in f"{action} {response}".lower(): return True
        return beat.actual_turns_taken >= beat.estimated_turns
    
    def _get_story_hint(self, beat_type: BeatType) -> str:
        """Subtle story hint for player"""
        hints = {
            BeatType.CATALYST: "You sense something important is about to happen...",
            BeatType.MIDPOINT: "The situation shifts dramatically...",
            BeatType.ALL_IS_LOST: "Things look dire...",
            BeatType.FINALE: "This feels like the moment of truth...",
        }
        return hints.get(beat_type, "")
    
    def _extract_entities(self, text: str) -> list:
        """Extract proper nouns - tylko nazwy własne, NIE polskie słowa"""
        entities = []
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        polish_endings = ['em', 'ą', 'ę', 'ami', 'owi', 'ach', 'om', 'cie', 'ina', 'ana', 'ego', 'ych']
        polish_words = ['Pytam', 'Idę', 'Mówię', 'Patrzę', 'Chodź', 'Chcę']
        
        for noun in proper_nouns:
            if any(noun.lower().endswith(ending) for ending in polish_endings): continue
            if noun in polish_words: continue
            entities.append(noun)
        
        return list(set(entities))
    
    def _extract_and_add_npcs_from_text(
        self,
        text: str,
        world_state: WorldState,
        validator,
        turn: int
    ):
        """Extract NPC names and races from generated text"""
        patterns = [
            r'([A-Z][a-z]+),\s+an?\s+([A-Z][a-z\']+)\s+([a-z]+)',
            r'([A-Z][a-z\']+)\s+named\s+([A-Z][a-z]+)',
            r'([A-Z][a-z\']+)\s+([a-z]+)\s+named\s+([A-Z][a-z]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 3:
                    if ',' in pattern: name, race, role = match
                    else: race, role, name = match
                    if role in ['on', 'in', 'at', 'to', 'from']: continue
                elif len(match) == 2: race, name = match; role = "unknown"
                else: continue
                
                if validator.validate_species(race):
                    if name not in world_state.npcs:
                        world_state.add_npc(
                            name=name, race=race, role=role,
                            location=world_state.current_location.name if world_state.current_location else "starting area",
                            turn=turn, notes=f"First mentioned in turn {turn}"
                        )
                        logger.info(f"👤 Added NPC: {name} ({race} {role})")
                    else:
                        world_state.update_npc(name, last_seen_turn=turn)
                        logger.info(f"👤 Updated NPC: {name} (last seen: turn {turn})")
    
    def _extract_planet_from_text(
        self,
        text: str,
        validator,
        default_planet: str
    ) -> str:
        """Extract which planet/moon the intro takes place on"""
        planet_patterns = [
            r'\bon\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
            r'\bat\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
            r'\barrives?\s+(?:at|on)\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
            r'\blands?\s+on\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
            r'\breaches?\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
            r'\bmoon.*?([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
            r'\bworld\s+of\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
        ]
        
        if 'nar shaddaa' in text.lower() and 'moon' in text.lower():
            logger.debug("🌙 Detected Nar Shaddaa (moon)")
            return 'Nar Shaddaa'
        
        for pattern in planet_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for potential_planet in matches:
                potential_planet = potential_planet.strip()
                if validator.validate_planet(potential_planet):
                    logger.debug(f"🌍 Extracted planet: {potential_planet}")
                    return potential_planet
        
        logger.debug(f"🌍 No planet detected, using default: {default_planet}")
        return default_planet