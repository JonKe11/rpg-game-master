# backend/app/services/story_aware_game_master.py
"""
Game Master ze świadomością story arc
Wie w którym momencie kampanii jesteśmy i dostosowuje narrację
"""
from typing import Dict
from datetime import datetime
from app.services.campaign_planner import CampaignPlanner
from app.services.campaign_structure import CampaignArc, BeatType
from app.core.ai.adaptive_game_master import AdaptiveGameMaster
from app.services.session_storage import SessionStorage
from app.services.wiki_fetcher_service import WikiFetcherService
from app.core.ai.canon_validator import CanonValidator
import re
from app.services.world_state import WorldState

class StoryAwareGameMaster:
    """
    Enhanced GM z:
    - Story arc tracking
    - RAG (wiki knowledge)
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
        self.wiki_fetcher = WikiFetcherService()
        self.validator = None  # Lazy init per universe
    
    def _get_validator(self, universe: str) -> CanonValidator:
        """Get validator for universe (lazy init)"""
        if self.validator is None or self.validator.universe != universe:
            print(f"🔧 Initializing Canon Validator for {universe}...")
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
        
        # 🆕 PROTECTION: Check if intro already exists
        existing_intro = self.storage.get_intro(session_id)
        if existing_intro:
            print(f"⚠️ Intro already exists for session {session_id} - returning cached")
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
        
        print(f"📖 Starting NEW campaign for {character_data['name']}...")
        
        # Get validator
        validator = self._get_validator(universe)
        
        # 1. Validate & fix character data
        if character_data.get('race'):
            if not validator.validate_species(character_data['race']):
                print(f"⚠️ Invalid species: {character_data['race']}")
                similar = validator.search_similar_canon(character_data['race'], 'species')
                if similar:
                    print(f"   💡 Did you mean: {similar}?")
                character_data['race'] = validator.get_fallback_species()
                print(f"   → Using: {character_data['race']}")
        
        homeworld = character_data.get('homeworld')
        if homeworld and not validator.validate_planet(homeworld):
            print(f"⚠️ Invalid planet: {homeworld}")
            similar = validator.search_similar_canon(homeworld, 'planet')
            if similar:
                print(f"   💡 Did you mean: {similar}?")
            homeworld = validator.get_fallback_planet()
            print(f"   → Using: {homeworld}")
        
        if not homeworld:
            homeworld = validator.get_fallback_planet()
        
        # 1b. FETCH RICH CONTEXT from wiki
        location_context = self.wiki_fetcher.fetch_context_for_location(homeworld, universe)
        
        capital_city = None
        if location_context.get('structured'):
            capital_city = location_context['structured'].get('capital')
        
        if capital_city:
            print(f"🏛️ Capital city: {capital_city}")
        else:
            print(f"🏛️ Capital city: Not specified in wiki (AI can choose location freely)")
        
        # 1c. CREATE WORLD STATE
        world_state = WorldState(
            universe=universe,
            starting_planet=homeworld,
            capital_city=capital_city,
            homeworld=homeworld
        )
        
        # Save world state immediately
        self.storage.save_world_state(session_id, world_state)
        print(f"💾 World State created and saved")
        
        # 2. Generate campaign
        print(f"📖 Planning {campaign_length} campaign...")
        campaign = self.campaign_planner.generate_campaign(
            character_data,
            universe,
            campaign_length
        )
        
        # 3. Save campaign
        self.storage.save_campaign(session_id, campaign)
        
        print(f"✅ Campaign: '{campaign.title}'")
        print(f"   Theme: {campaign.main_theme}")
        print(f"   Turns: {campaign.total_estimated_turns}")
        
        current_beat = campaign.get_current_beat()
        
        # 4. Fetch wiki context - BUILD RICH CONTEXT
        race_wiki = None
        if character_data.get('race'):
            race_wiki = self.wiki_fetcher.fetch_article(character_data['race'], universe)
        
        # Build RICH wiki context with structured data
        wiki_data_with_structure = {}
        
        if race_wiki:
            wiki_data_with_structure[character_data['race']] = race_wiki
        
        if location_context.get('location'):
            wiki_data_with_structure[homeworld] = {
                **location_context['location'],
                'structured': location_context.get('structured', {})
            }
        
        wiki_context = self._build_rich_wiki_context(wiki_data_with_structure)
        
        # 5b. GET WORLD CONTEXT
        world_context = world_state.get_world_context_for_prompt()
        
        # 6. 🆕 SIMPLIFIED PROMPT - No lists, rich wiki context
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
3. If no specific cities mentioned, create a vivid location:
   - "in the forests of Endor"
   - "among the hills of Aldhani"  
   - "in the desert wastes"
   - "at a remote settlement"

CREATIVE FREEDOM:
- Use wiki data as foundation (planet types, terrain, what orbits what)
- Create specific unnamed locations within canon places
- If character not on homeworld, briefly mention why

LANGUAGE: English only
FORMAT: 2-3 sentence immersive intro

Write the intro:"""
        
        print("🎨 Generating intro with AI...")
        intro_text = self.gm._generate_llm_response(intro_prompt, "")
        
        # EXTRACT actual starting planet from AI response
        actual_starting_planet = self._extract_planet_from_text(intro_text, validator, homeworld)
        if actual_starting_planet and actual_starting_planet != homeworld:
            print(f"🌍 AI chose starting planet: {actual_starting_planet} (homeworld: {homeworld})")
            world_state.starting_planet = actual_starting_planet
            world_state.current_planet = actual_starting_planet
            
            # Fetch rich context for the ACTUAL starting planet
            actual_location_context = self.wiki_fetcher.fetch_context_for_location(actual_starting_planet, universe)
            if actual_location_context.get('structured'):
                actual_capital = actual_location_context['structured'].get('capital')
                if actual_capital:
                    world_state.capital_city = actual_capital
                    print(f"🏛️ Updated capital for {actual_starting_planet}: {world_state.capital_city}")
        else:
            print(f"🌍 Starting on homeworld: {homeworld}")
        
        # 7. VALIDATE generated intro
        validation = validator.scan_and_validate(intro_text)
        
        serious_violations = [
            v for v in validation['invalid']
            if len(v) > 6 or v.endswith(('ian', 'ite', 'ese', 'ish', 'oid'))
        ]
        
        if serious_violations:
            print(f"⚠️ SERIOUS VIOLATIONS detected: {serious_violations}")
            print("🔄 Regenerating with ultra-safe fallback...")
            intro_text = self._generate_safe_intro(character_data, world_state.current_planet, campaign)
        else:
            print(f"✅ Intro validated - no serious violations!")
        
        # 7b. 🆕 WIKI-BASED FACT-CHECK
        fact_check = self._fact_check_response(intro_text, universe, validator, wiki_data_with_structure)
        
        if not fact_check['valid']:
            print(f"🚨 FACT-CHECK FAILED: {fact_check['errors']}")
            print("🔄 Regenerating with corrections...")
            intro_text = self._generate_safe_intro(character_data, world_state.current_planet, campaign)
        else:
            print("✅ Fact-check passed!")
        
        # 7c. CHECKPOINT VALIDATION
        checkpoint = self._validate_response_consistency(intro_text, world_state, validator)
        
        if not checkpoint['valid']:
            print(f"🚨 CHECKPOINT FAILED: {checkpoint['violations']}")
            
            if checkpoint['severity'] == 'critical':
                print("🔄 Critical issue - regenerating...")
                intro_text = self._generate_safe_intro(character_data, world_state.current_planet, campaign)
            else:
                print("🔧 Attempting auto-fix...")
                intro_text = self._fix_response(intro_text, world_state, validator)
        else:
            print("✅ Checkpoint passed!")
        
        # 7d. UPDATE WORLD STATE after successful intro
        world_state.add_event(
            f"Campaign '{campaign.title}' started on {world_state.current_planet}",
            turn=0
        )
        
        # 7e. EXTRACT NPCs from intro
        self._extract_and_add_npcs_from_text(
            intro_text, 
            world_state, 
            validator, 
            turn=0
        )
        
        # Save updated world state
        self.storage.save_world_state(session_id, world_state)
        
        # 8. Save intro permanently
        intro_data = {
            'message': intro_text,
            'type': 'narration',
            'location': world_state.current_planet,
            'timestamp': datetime.now().isoformat(),
            'validated': True,
            'validation_result': validation
        }
        self.storage.save_intro(session_id, intro_data)
        print(f"💾 Intro saved for session {session_id}")
        
        return {
            'message': intro_text,
            'type': 'narration',
            'location': world_state.current_planet,
            'timestamp': datetime.now().isoformat(),
            'campaign': {
                'title': campaign.title,
                'theme': campaign.main_theme,
                'progress': 0,
                'current_beat': current_beat.title if current_beat else None,
                'estimated_turns': campaign.total_estimated_turns
            }
        }
        
    def _generate_safe_intro(self, character_data: Dict, planet: str, campaign) -> str:
        """Ultra-safe intro when validation fails - uses only verified elements"""
        
        # Safe intro templates for different planets
        safe_intros = {
            'Tatooine': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} who has arrived on the desert world of Tatooine. The twin suns beat down mercilessly as you step into the dusty streets of Mos Eisley, where spacers and smugglers conduct their shadowy business.",
            
            'Coruscant': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} navigating the endless cityscape of Coruscant. Towering skyscrapers stretch into the polluted sky as speeders zip past overhead. Your journey begins in the bustling lower levels.",
            
            'Nar Shaddaa': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} who has come to Nar Shaddaa, the moon known as the Smuggler's Moon. Neon lights flicker in the perpetual twilight as you walk through crowded streets filled with criminals and outcasts from across the galaxy.",
            
            'Nal Hutta': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} on the polluted swamp world of Nal Hutta, homeworld of the Hutts. The air is thick with moisture and industrial smog as you navigate the grimy settlements.",
            
            'Aldhani': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} on Aldhani. The rugged hills stretch before you as you make your way through the remote terrain. Your journey is about to begin.",
            
            'default': f"You are {character_data['name']}, a {character_data.get('race', 'Human')} beginning your journey on {planet}. The adventure ahead will test your skills and resolve."
        }
        
        return safe_intros.get(planet, safe_intros['default'])
    
    def process_action_with_story(
        self,
        session_id: int,
        action: str
    ) -> Dict:
        """Process action with World State tracking and story arc awareness"""
        
        # 1. Load campaign
        campaign = self.storage.get_campaign(session_id)
        if not campaign:
            return {'error': 'Campaign not found'}
        
        # 1b. LOAD WORLD STATE
        world_state = self.storage.get_world_state(session_id)
        if not world_state:
            print("⚠️ World state not found - creating new one")
            world_state = WorldState(
                universe=campaign.universe,
                starting_planet="Tatooine",
                capital_city=None
            )
            self.storage.save_world_state(session_id, world_state)
        
        # Get validator
        validator = self._get_validator(campaign.universe)
        
        current_beat = campaign.get_current_beat()
        current_turn = campaign.current_turn
        
        # 2. Extract entities from action
        entities = self._extract_entities(action)
        
        # 3. Fetch relevant wiki (only canon) with RICH context
        wiki_data = {}
        for entity in entities[:2]:  # Max 2 per turn
            article = self.wiki_fetcher.fetch_article(entity, campaign.universe)
            if article and article.get('is_canon', True):
                wiki_data[entity] = article
        
        # 4. Build RICH context for AI
        wiki_context = self._build_rich_wiki_context(wiki_data)
        
        # 5. GET WORLD CONTEXT
        world_context = world_state.get_world_context_for_prompt()
        
        # 6. 🆕 SIMPLIFIED PROMPT - No lists!
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
        
        # 7. VALIDATE response
        validation = validator.scan_and_validate(response_text)
        
        serious = [v for v in validation['invalid'] if len(v) > 6]
        if serious:
            print(f"⚠️ Serious invalid entities: {serious}")
        
        # 7a. WIKI-BASED FACT-CHECK
        fact_check = self._fact_check_response(response_text, campaign.universe, validator, wiki_data)
        if not fact_check['valid']:
            print(f"⚠️ Fact-check issues: {fact_check['errors'][:2]}")
        
        # 7b. CHECKPOINT VALIDATION
        checkpoint = self._validate_response_consistency(response_text, world_state, validator)
        
        if not checkpoint['valid']:
            print(f"🚨 CHECKPOINT: {checkpoint['violations']} (severity: {checkpoint['severity']})")
            
            # Try auto-fix first
            original_response = response_text
            response_text = self._fix_response(response_text, world_state, validator)
            
            # Check if we should regenerate
            if self._should_regenerate(checkpoint, response_text):
                print("🔄 Regenerating response...")
                
                retry_prompt = f"""You made mistakes. Retry with EXACT requirements:

{world_context}

Player: "{action}"

CRITICAL: 
- Stay on planet {world_state.current_planet}
- Use existing NPCs if relevant
- Respond in ENGLISH ONLY
- DO NOT output metadata

Response (2-4 sentences):"""
                
                response_text = self.gm._generate_llm_response(retry_prompt, "")
                print("✅ Regenerated")
            else:
                if response_text != original_response:
                    print("✅ Auto-fixed")
        else:
            print("✅ Checkpoint passed")
        
        # 7c. UPDATE WORLD STATE
        world_state.add_event(
            f"Player: {action[:50]}{'...' if len(action) > 50 else ''}",
            turn=current_turn
        )
        
        # 7d. EXTRACT any new NPCs from response
        self._extract_and_add_npcs_from_text(
            response_text,
            world_state,
            validator,
            turn=current_turn
        )
        
        # 8. Update beat progress
        if current_beat:
            current_beat.actual_turns_taken += 1
            
            should_advance = self._should_advance_beat(
                current_beat, action, response_text
            )
            
            if should_advance:
                print(f"📖 Beat completed: {current_beat.title}")
                campaign.advance_beat()
                
                world_state.add_memory_trace(
                    f"Story beat completed: {current_beat.title}",
                    turn=current_turn,
                    is_critical=True
                )
                
                next_beat = campaign.get_current_beat()
                if next_beat:
                    hint = self._get_story_hint(next_beat.beat_type)
                    if hint:
                        response_text += f"\n\n*{hint}*"
        
        # 9. Update campaign
        campaign.current_turn += 1
        campaign.last_updated = datetime.now()
        self.storage.save_campaign(session_id, campaign)
        
        # 9b. SAVE WORLD STATE
        self.storage.save_world_state(session_id, world_state)
        
        # 10. Build response
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
                'turns_total': campaign.total_estimated_turns,
                'near_end': campaign.is_near_end(),
                'completed': campaign.is_completed()
            }
        }
    
    # ========================================================================
    # 🆕 NEW: Rich Wiki Context Builder
    # ========================================================================
    
    def _build_rich_wiki_context(self, wiki_data: Dict) -> str:
        """
        Build RICH context from wiki - structured and detailed
        Shows relationships, terrain, capitals, moons - everything AI needs
        """
        if not wiki_data:
            return "No wiki data available. Use your knowledge of the universe."
        
        parts = []
        
        for title, article in wiki_data.items():
            if not article:
                continue
            
            # Skip non-canon
            if not article.get('is_canon', True):
                continue
            
            # Build rich context block
            context_block = f"\n{'='*60}\n"
            context_block += f"📖 ARTICLE: {title}\n"
            context_block += f"{'='*60}\n"
            
            # Description
            if article.get('description'):
                context_block += f"\nDESCRIPTION:\n{article['description'][:400]}\n"
            
            # Structured info (if location)
            if 'structured' in article:
                struct = article['structured']
                
                context_block += f"\nSTRUCTURED INFO:\n"
                
                if struct.get('type'):
                    context_block += f"- Type: {struct['type']}\n"
                
                if struct.get('capital'):
                    context_block += f"- Capital: {struct['capital']}\n"
                
                if struct.get('orbits'):
                    context_block += f"- Orbits: {struct['orbits']} (this is a moon!)\n"
                
                if struct.get('moons'):
                    context_block += f"- Moons: {', '.join(struct['moons'])}\n"
                
                if struct.get('terrain'):
                    context_block += f"- Terrain: {', '.join(struct['terrain'])}\n"
            
            # Info box highlights
            if article.get('info_box') and isinstance(article['info_box'], dict):
                relevant_keys = ['population', 'government', 'species', 'language']
                info_items = []
                
                for key, value in article['info_box'].items():
                    if any(rk in key.lower() for rk in relevant_keys):
                        info_items.append(f"{key}: {value}")
                
                if info_items:
                    context_block += f"\nADDITIONAL INFO:\n"
                    for item in info_items[:5]:  # Max 5
                        context_block += f"- {item}\n"
            
            parts.append(context_block)
        
        return "\n".join(parts) if parts else "No detailed wiki data. Use general universe knowledge."
    
    # ========================================================================
    # 🆕 NEW: Wiki-Based Fact Checking
    # ========================================================================
    
    def _fact_check_response(
        self,
        text: str,
        universe: str,
        validator,
        wiki_context_data: Dict = None
    ) -> Dict[str, any]:
        """
        Fact-check response using ACTUAL WIKI DATA
        Not hardcoded rules - checks against what wiki says
        """
        errors = []
        corrections = {}
        
        if not wiki_context_data:
            return {'valid': True, 'errors': [], 'corrections': {}}
        
        # Extract structured info from wiki data
        for title, article in wiki_context_data.items():
            if not article:
                continue
            
            struct = article.get('structured', {})
            location_name = title.lower()
            
            # Check if AI contradicts wiki data
            if location_name in text.lower():
                
                # 1. Check type (planet vs moon)
                if struct.get('type') == 'moon':
                    # Make sure AI doesn't call it a planet or city
                    wrong_phrases = [
                        f'{title.lower()}.*planet',
                        f'planet.*{title.lower()}',
                        f'{title.lower()}.*city.*capital',
                        f'capital.*{title.lower()}.*city',
                    ]
                    
                    for phrase in wrong_phrases:
                        if re.search(phrase, text.lower()):
                            if struct.get('orbits'):
                                errors.append(f"{title} is a moon orbiting {struct['orbits']}, not a planet")
                            else:
                                errors.append(f"{title} is a moon, not a planet")
                
                # 2. Check capital
                if struct.get('capital'):
                    wiki_capital = struct['capital'].lower()
                    
                    # Look for wrong capital mentions
                    capital_pattern = f'{location_name}.*capital.*?([A-Z][a-z]+)'
                    matches = re.findall(capital_pattern, text, re.IGNORECASE)
                    
                    for mentioned_capital in matches:
                        if mentioned_capital.lower() != wiki_capital and mentioned_capital.lower() != title.lower():
                            errors.append(f"Wiki says capital of {title} is {struct['capital']}, not {mentioned_capital}")
                            corrections[mentioned_capital] = struct['capital']
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'corrections': corrections
        }
    
    # ========================================================================
    # Checkpoint Validation System
    # ========================================================================
    
    def _validate_response_consistency(
        self,
        response: str,
        world_state: WorldState,
        validator
    ) -> Dict[str, any]:
        """
        Checkpoint validation - sprawdź czy AI nie namieszał
        Returns: {'valid': bool, 'violations': list, 'severity': str}
        """
        violations = []
        severity = 'none'  # none, minor, major, critical
        
        # 1. Check planet consistency
        if world_state.current_planet:
            other_planets = validator.get_canon_planets(limit=100)
            wrong_planets_mentioned = []
            
            for planet in other_planets:
                if planet == world_state.current_planet:
                    continue
                
                if planet.lower() in response.lower():
                    wrong_planets_mentioned.append(planet)
            
            if wrong_planets_mentioned:
                violations.append(f"Mentioned wrong planet(s): {wrong_planets_mentioned}")
                severity = 'critical'
        
        # 2. Check NPC consistency (race changes)
        for npc_name, npc_data in world_state.npcs.items():
            if npc_name in response:
                correct_race = npc_data.race
                other_races = validator.get_canon_species(limit=50)
                
                for race in other_races:
                    if race != correct_race and race.lower() in response.lower():
                        pattern = f"{npc_name}.{{0,50}}{race}|{race}.{{0,50}}{npc_name}"
                        if re.search(pattern, response, re.IGNORECASE):
                            violations.append(f"Changed {npc_name}'s race from {correct_race} to {race}")
                            severity = max(severity, 'major', key=['none', 'minor', 'major', 'critical'].index)
        
        # 3. Check if AI leaked metadata
        metadata_keywords = [
            'aktualny stan świata', 'world state', 'established facts',
            'memory traces', 'turn 0:', 'turn 1:',
            '**miejsce:**', '**data:**', 'current location:', 'known npcs:',
        ]
        
        for keyword in metadata_keywords:
            if keyword.lower() in response.lower():
                violations.append(f"Leaked metadata: '{keyword}'")
                severity = max(severity, 'minor', key=['none', 'minor', 'major', 'critical'].index)
        
        # 4. Check language (detect Polish)
        polish_indicators = ['ą', 'ę', 'ć', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
        if any(char in response for char in polish_indicators):
            violations.append("Response contains non-English text (Polish detected)")
            severity = max(severity, 'major', key=['none', 'minor', 'major', 'critical'].index)
        
        return {
            'valid': len(violations) == 0 or severity == 'minor',
            'violations': violations,
            'severity': severity
        }
        
    def _fix_response(
        self,
        response: str,
        world_state: WorldState,
        validator
    ) -> str:
        """Auto-fix common mistakes in response"""
        fixed = response
        
        # 1. Fix planet mentions
        if world_state.current_planet:
            wrong_planets = validator.get_canon_planets(limit=100)
            for wrong_planet in wrong_planets:
                if wrong_planet != world_state.current_planet:
                    pattern = re.compile(re.escape(wrong_planet), re.IGNORECASE)
                    fixed = pattern.sub(world_state.current_planet, fixed)
        
        # 2. Remove metadata leaks
        fixed = re.sub(
            r'\*\*Aktualny stan świata:\*\*.*?(?=\n\n|\Z)',
            '', fixed, flags=re.DOTALL | re.IGNORECASE
        )
        
        fixed = re.sub(
            r'\n- (Miejsce|Data|Godzina|Turn|Beat):.*',
            '', fixed, flags=re.IGNORECASE
        )
        
        fixed = re.sub(
            r'\*\*(Wydane polecenia|Znajomi NPC):\*\*.*?(?=\n\n|\Z)',
            '', fixed, flags=re.DOTALL | re.IGNORECASE
        )
        
        # Clean up extra whitespace
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
        
        if severity == 'critical':
            return True
        
        if severity == 'major':
            if len(response.strip()) < 50:
                return True
            if any('Polish' in v or 'non-English' in v for v in validation_result['violations']):
                return True
            return False
        
        return False
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _should_advance_beat(self, beat, action: str, response: str) -> bool:
        """Decide if beat should advance"""
        
        # Minimum turns increased to 3
        if beat.actual_turns_taken < max(3, beat.estimated_turns - 2):
            return False
        
        # Force advance after max
        if beat.actual_turns_taken >= beat.estimated_turns + 3:
            return True
        
        # Keyword trigger
        if beat.trigger_keyword:
            combined = f"{action} {response}".lower()
            if beat.trigger_keyword in combined:
                return True
        
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
        
        # Filtruj polskie słowa
        polish_endings = ['em', 'ą', 'ę', 'ami', 'owi', 'ach', 'om', 'cie', 'ina', 'ana', 'ego', 'ych']
        polish_words = ['Pytam', 'Idę', 'Mówię', 'Patrzę', 'Chodź', 'Chcę']
        
        for noun in proper_nouns:
            if any(noun.lower().endswith(ending) for ending in polish_endings):
                continue
            if noun in polish_words:
                continue
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
            r'([A-Z][a-z]+),\s+an?\s+([A-Z][a-z\']+)\s+([a-z]+)',  # "Kael, a Twi'lek smuggler"
            r'([A-Z][a-z\']+)\s+named\s+([A-Z][a-z]+)',  # "Twi'lek named Kael"
            r'([A-Z][a-z\']+)\s+([a-z]+)\s+named\s+([A-Z][a-z]+)',  # "Twi'lek smuggler named Kael"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) == 3:
                    if ',' in pattern:  # Pattern 1
                        name, race, role = match
                    else:  # Pattern 3
                        race, role, name = match
                    
                    # Skip false positives
                    if role in ['on', 'in', 'at', 'to', 'from']:
                        continue
                        
                elif len(match) == 2:  # Pattern 2
                    race, name = match
                    role = "unknown"
                else:
                    continue
                
                # Validate race is canon
                if validator.validate_species(race):
                    if name not in world_state.npcs:
                        world_state.add_npc(
                            name=name,
                            race=race,
                            role=role,
                            location=world_state.current_location.name if world_state.current_location else "starting area",
                            turn=turn,
                            notes=f"First mentioned in turn {turn}"
                        )
                        print(f"👤 Added NPC: {name} ({race} {role})")
                    else:
                        world_state.update_npc(name, last_seen_turn=turn)
                        print(f"👤 Updated NPC: {name} (last seen: turn {turn})")
    
    def _extract_planet_from_text(
        self,
        text: str,
        validator,
        default_planet: str
    ) -> str:
        """Extract which planet/moon the intro takes place on"""
        
        planet_patterns = [
            r'\bon\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',  # "on Nar Shaddaa"
            r'\bat\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',  # "at Coruscant"
            r'\barrives?\s+(?:at|on)\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
            r'\blands?\s+on\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
            r'\breaches?\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',
            r'\bmoon.*?([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',  # "moon of Nar Shaddaa"
            r'\bworld\s+of\s+([A-Z][a-z\']+(?:\s+[A-Z][a-z]+)?)\b',  # "world of Tatooine"
        ]
        
        # Check for explicit "Nar Shaddaa, the moon" mentions
        if 'nar shaddaa' in text.lower() and 'moon' in text.lower():
            print("🌙 Detected Nar Shaddaa (moon)")
            return 'Nar Shaddaa'
        
        for pattern in planet_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for potential_planet in matches:
                potential_planet = potential_planet.strip()
                
                if validator.validate_planet(potential_planet):
                    print(f"🌍 Extracted planet: {potential_planet}")
                    return potential_planet
        
        print(f"🌍 No planet detected, using default: {default_planet}")
        return default_planet     