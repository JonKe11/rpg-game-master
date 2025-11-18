# backend/app/services/campaign_planner.py
"""
AI generuje strukturę kampanii na początku sesji
Używa wiki context z PostgreSQL dla inspiracji
"""
from typing import Dict, List
import json
import re
import logging
from app.services.campaign_structure import (
    CampaignArc, StoryBeat, StoryAct, BeatType
)
# ⛔️ USUNIĘTE: from app.services.wiki_fetcher_service import WikiFetcherService
from app.core.ai.adaptive_game_master import AdaptiveGameMaster

# ✅ NOWE IMPORTY
from app.models.database import SessionLocal
from app.services.postgres_cache_service import PostgresCacheService

logger = logging.getLogger(__name__)

class CampaignPlanner:
    """
    Planuje całą kampanię używając AI + wiki knowledge z PostgreSQL
    """
    
    def __init__(self, game_master: AdaptiveGameMaster):
        self.gm = game_master
        
        # ✅ NOWA LOGIKA: Dostęp do bazy danych PostgreSQL
        try:
            self.db = SessionLocal()
            self.pg_cache = PostgresCacheService(self.db)
            logger.info("✅ CampaignPlanner połączony z PostgresCacheService")
        except Exception as e:
            logger.error(f"❌ CampaignPlanner nie mógł połączyć się z DB: {e}")
            self.db = None
            self.pg_cache = None
    
    def __del__(self):
        if self.db:
            self.db.close()
            
    def generate_campaign(
        self, 
        character: Dict, 
        universe: str,
        desired_length: str = "medium"
    ) -> CampaignArc:
        """
        Generuje pełną strukturę kampanii
        """
        
        logger.info(f"📖 Planning {desired_length} campaign for {character['name']}...")
        
        params = self._get_campaign_parameters(desired_length)
        wiki_context = self._gather_wiki_inspiration(character, universe)
        campaign_outline = self._generate_outline_with_ai(
            character, universe, params, wiki_context
        )
        beats = self._create_story_beats(campaign_outline, params)
        
        arc = CampaignArc(
            campaign_id=f"camp_{character['id']}_{universe}",
            title=campaign_outline['title'],
            universe=universe,
            main_theme=campaign_outline['theme'],
            main_antagonist=campaign_outline['antagonist'],
            final_goal=campaign_outline['goal'],
            total_estimated_turns=params['total_turns'],
            beats=beats,
            current_beat_id=beats[0].id if beats else None
        )
        
        if beats:
            beats[0].status = "active"
        
        return arc
    
    def _get_campaign_parameters(self, length: str) -> Dict:
        """Parametry dla różnych długości"""
        params = {
            'short': {'total_turns': 18, 'num_beats': 12},
            'medium': {'total_turns': 35, 'num_beats': 18},
            'long': {'total_turns': 60, 'num_beats': 25}
        }
        return params.get(length, params['medium'])
    
    def _gather_wiki_inspiration(self, character: Dict, universe: str) -> str:
        """✅ ZMODYFIKOWANE: Zbiera wiki articles dla inspiracji AI z PostgreSQL"""
        
        if not self.pg_cache:
            return "Brak połączenia z bazą danych Wiki."
            
        elements = []
        
        try:
            # Race info
            if character.get('race'):
                article = self.pg_cache.get_article_by_title(character['race'], universe)
                if article and article.content:
                    elements.append(f"Race ({character['race']}): {article.content.get('description', '')[:200]}")
            
            # Homeworld info
            if character.get('homeworld'):
                article = self.pg_cache.get_article_by_title(character['homeworld'], universe)
                if article and article.content:
                    elements.append(f"Homeworld ({character['homeworld']}): {article.content.get('description', '')[:200]}")
            
            # Get organizations for antagonist ideas
            results = self.pg_cache.search_articles_paginated(
                universe=universe,
                category="organizations",
                limit=10,
                offset=0
            )
            orgs = [a.title for a in results['items']]
            if orgs:
                elements.append(f"Possible antagonists (Organizations): {', '.join(orgs[:5])}")
                
        except Exception as e:
            logger.error(f"Nie udało się zebrać inspiracji z Wiki: {e}")
            return "Błąd podczas pobierania danych kanonu."
        
        return "\n".join(elements) if elements else "No wiki context available"
    
    def _generate_outline_with_ai(
        self, 
        character: Dict, 
        universe: str,
        params: Dict,
        wiki_context: str
    ) -> Dict:
        """AI generuje ogólny outline kampanii"""
        
        prompt = f"""You are an RPG campaign designer for {universe}.

CHARACTER:
- Name: {character['name']}
- Race: {character.get('race', 'Unknown')}
- Class: {character.get('class_type', 'Adventurer')}
- Level: {character.get('level', 1)}

WIKI CONTEXT (use for canon elements, especially antagonists):
{wiki_context}

CAMPAIGN:
- Length: {params['total_turns']} turns
- Structure: 3-act story

Create campaign outline with:
1. title: Engaging campaign name
2. theme: One word (revenge/discovery/redemption/survival)
3. antagonist: Main villain (from wiki context if possible)
4. goal: What player must accomplish
5. hook: Act 1 inciting incident
6. twist: Act 2 midpoint surprise
7. climax: Act 3 final confrontation

RULES:
- Use ONLY canon wiki elements from the context provided
- Make it personal to character
- Keep antagonist credible
- Ensure logical progression

Return ONLY valid JSON:
{{
    "title": "...",
    "theme": "...",
    "antagonist": "...",
    "goal": "...",
    "hook": "...",
    "twist": "...",
    "climax": "..."
}}"""
        
        response = self.gm._generate_llm_response(prompt, universe)
        
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.warning(f"AI JSON parse failed: {e}. Response was: {response}")
        
        # Fallback
        return {
            'title': f"The {character.get('name', 'Hero')} Chronicles",
            'theme': 'discovery',
            'antagonist': 'Imperial Forces',
            'goal': 'Stop the threat',
            'hook': 'Mysterious message arrives',
            'twist': 'Ally betrays you',
            'climax': 'Final confrontation'
        }
    
    def _create_story_beats(self, outline: Dict, params: Dict) -> List[StoryBeat]:
        """Tworzy konkretne story beats"""
        beats = []
        beat_id = 0
        total_turns = params['total_turns']
        
        act1_turns = int(total_turns * 0.22)
        act2_turns = int(total_turns * 0.50)
        act3_turns = int(total_turns * 0.22)
        epilogue_turns = total_turns - act1_turns - act2_turns - act3_turns
        
        # ACT 1: Setup
        act1_beats = [
            StoryBeat(
                id=f"beat_{beat_id:02d}", beat_type=BeatType.OPENING_IMAGE,
                act=StoryAct.ACT_1_SETUP, title="Opening: Normal World",
                description="Character's ordinary life before adventure",
                estimated_turns=max(2, act1_turns // 4)
            ),
            StoryBeat(
                id=f"beat_{beat_id+1:02d}", beat_type=BeatType.CATALYST,
                act=StoryAct.ACT_1_SETUP, title="Catalyst",
                description=outline.get('hook', 'Inciting incident disrupts normalcy'),
                estimated_turns=max(2, act1_turns // 4)
            ),
            StoryBeat(
                id=f"beat_{beat_id+2:02d}", beat_type=BeatType.DEBATE,
                act=StoryAct.ACT_1_SETUP, title="Debate",
                description="Character debates whether to get involved",
                estimated_turns=max(1, act1_turns // 4)
            ),
            StoryBeat(
                id=f"beat_{beat_id+3:02d}", beat_type=BeatType.BREAK_INTO_TWO,
                act=StoryAct.ACT_1_SETUP, title="Commitment",
                description="Character commits to the quest",
                estimated_turns=max(1, act1_turns // 4)
            )
        ]
        beats.extend(act1_beats)
        beat_id += len(act1_beats)
        
        # ACT 2: Confrontation
        act2_beats = [
            StoryBeat(
                id=f"beat_{beat_id:02d}", beat_type=BeatType.FUN_AND_GAMES,
                act=StoryAct.ACT_2_CONFRONTATION, title="Adventure Begins",
                description="Explore the world and the premise",
                estimated_turns=max(3, act2_turns // 4)
            ),
            StoryBeat(
                id=f"beat_{beat_id+1:02d}", beat_type=BeatType.MIDPOINT,
                act=StoryAct.ACT_2_CONFRONTATION, title="Midpoint Twist",
                description=outline.get('twist', 'Major revelation changes everything'),
                estimated_turns=max(2, act2_turns // 4),
                trigger_keyword=outline.get('twist', '').lower()[:20]
            ),
            StoryBeat(
                id=f"beat_{beat_id+2:02d}", beat_type=BeatType.BAD_GUYS_CLOSE_IN,
                act=StoryAct.ACT_2_CONFRONTATION, title="Rising Tension",
                description=f"{outline.get('antagonist', 'Antagonist')} gains upper hand",
                estimated_turns=max(3, act2_turns // 4)
            ),
            StoryBeat(
                id=f"beat_{beat_id+3:02d}", beat_type=BeatType.ALL_IS_LOST,
                act=StoryAct.ACT_2_CONFRONTATION, title="All Is Lost",
                description="Major setback - seems impossible",
                estimated_turns=max(2, act2_turns // 4)
            )
        ]
        beats.extend(act2_beats)
        beat_id += len(act2_beats)
        
        # ACT 3: Resolution
        act3_beats = [
            StoryBeat(
                id=f"beat_{beat_id:02d}", beat_type=BeatType.BREAK_INTO_THREE,
                act=StoryAct.ACT_3_RESOLUTION, title="Revelation",
                description="Find solution/inner strength",
                estimated_turns=max(2, act3_turns // 3)
            ),
            StoryBeat(
                id=f"beat_{beat_id+1:02d}", beat_type=BeatType.FINALE,
                act=StoryAct.ACT_3_RESOLUTION, title="Final Battle",
                description=outline.get('climax', f"Confront {outline.get('antagonist', 'antagonist')}"),
                estimated_turns=max(3, act3_turns // 3),
                trigger_keyword=outline.get('antagonist', '').lower()
            ),
            StoryBeat(
                id=f"beat_{beat_id+2:02d}", beat_type=BeatType.FINAL_IMAGE,
                act=StoryAct.ACT_3_RESOLUTION, title="Resolution",
                description=outline.get('goal', 'Achieve the goal'),
                estimated_turns=max(1, act3_turns // 3)
            )
        ]
        beats.extend(act3_beats)
        beat_id += len(act3_beats)
        
        # EPILOGUE
        if epilogue_turns > 0:
            epilogue = StoryBeat(
                id=f"beat_{beat_id:02d}", beat_type=BeatType.FINAL_IMAGE,
                act=StoryAct.EPILOGUE, title="Epilogue",
                description="See consequences of choices",
                estimated_turns=epilogue_turns
            )
            beats.append(epilogue)
        
        return beats