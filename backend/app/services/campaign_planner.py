# backend/app/services/campaign_planner.py
"""
AI generuje strukturę kampanii na początku sesji
Używa wiki context dla inspiracji
"""
from typing import Dict, List
import json
import re
from app.services.campaign_structure import (
    CampaignArc, StoryBeat, StoryAct, BeatType
)
from app.services.wiki_fetcher_service import WikiFetcherService
from app.core.ai.adaptive_game_master import AdaptiveGameMaster

class CampaignPlanner:
    """
    Planuje całą kampanię używając AI + wiki knowledge
    """
    
    def __init__(self, game_master: AdaptiveGameMaster):
        self.gm = game_master
        self.wiki_fetcher = WikiFetcherService()
    
    def generate_campaign(
        self, 
        character: Dict, 
        universe: str,
        desired_length: str = "medium"
    ) -> CampaignArc:
        """
        Generuje pełną strukturę kampanii
        
        Args:
            character: Character data
            universe: star_wars, lotr, etc.
            desired_length: short (15-20), medium (30-40), long (50-70) turns
        """
        
        print(f"📖 Planning {desired_length} campaign for {character['name']}...")
        
        # 1. Get campaign parameters
        params = self._get_campaign_parameters(desired_length)
        
        # 2. Gather wiki context
        wiki_context = self._gather_wiki_inspiration(character, universe)
        
        # 3. Generate outline with AI
        campaign_outline = self._generate_outline_with_ai(
            character, universe, params, wiki_context
        )
        
        # 4. Create story beats
        beats = self._create_story_beats(campaign_outline, params)
        
        # 5. Build CampaignArc
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
        
        # Set first beat as active
        if beats:
            beats[0].status = "active"
        
        return arc
    
    def _get_campaign_parameters(self, length: str) -> Dict:
        """Parametry dla różnych długości"""
        params = {
            'short': {
                'total_turns': 18,
                'num_beats': 12
            },
            'medium': {
                'total_turns': 35,
                'num_beats': 18
            },
            'long': {
                'total_turns': 60,
                'num_beats': 25
            }
        }
        return params.get(length, params['medium'])
    
    def _gather_wiki_inspiration(self, character: Dict, universe: str) -> str:
        """Zbiera wiki articles dla inspiracji AI"""
        
        elements = []
        
        # Race info
        if character.get('race'):
            race_article = self.wiki_fetcher.fetch_article(character['race'], universe)
            if race_article:
                elements.append(f"Race ({character['race']}): {race_article.get('description', '')[:200]}")
        
        # Homeworld info
        if character.get('homeworld'):
            planet = self.wiki_fetcher.fetch_article(character['homeworld'], universe)
            if planet:
                elements.append(f"Homeworld ({character['homeworld']}): {planet.get('description', '')[:200]}")
        
        # Get organizations for antagonist ideas
        from app.core.scraper.wiki_scraper import WikiScraper
        scraper = WikiScraper()
        orgs = scraper.get_all_organizations(universe)[:10]
        elements.append(f"Possible antagonists: {', '.join(orgs[:5])}")
        
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

WIKI CONTEXT (use for canon elements):
{wiki_context}

CAMPAIGN:
- Length: {params['total_turns']} turns
- Structure: 3-act story

Create campaign outline with:
1. title: Engaging campaign name
2. theme: One word (revenge/discovery/redemption/survival)
3. antagonist: Main villain (from wiki orgs if possible)
4. goal: What player must accomplish
5. hook: Act 1 inciting incident
6. twist: Act 2 midpoint surprise
7. climax: Act 3 final confrontation

RULES:
- Use ONLY canon wiki elements
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
        
        response = self.gm._generate_llm_response(prompt, "")
        
        # Try to parse JSON
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            print(f"⚠️ AI JSON parse failed: {e}")
        
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
        
        # Calculate act lengths (simplified)
        act1_turns = int(total_turns * 0.22)  # 22%
        act2_turns = int(total_turns * 0.50)  # 50%
        act3_turns = int(total_turns * 0.22)  # 22%
        epilogue_turns = total_turns - act1_turns - act2_turns - act3_turns  # Remaining
        
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