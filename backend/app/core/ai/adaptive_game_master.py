
# backend/app/core/ai/adaptive_game_master.py
import random
import re
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime
from enum import Enum
import ollama
import json
from app.core.scraper.wiki_scraper import WikiScraper

class NarrativeStyle(Enum):
    """Różne style prowadzenia narracji"""
    OPEN_WORLD = "open"          # Pełna wolność
    GUIDED = "guided"             # Delikatne sugestie
    CHOICES = "choices"           # Wybory wielokrotne
    CINEMATIC = "cinematic"       # Skryptowane wydarzenia
    
class StoryBeat(Enum):
    """Momenty fabularne"""
    INTRO = "intro"
    BUILD_UP = "build_up"
    CONFLICT = "conflict"
    CLIMAX = "climax"
    RESOLUTION = "resolution"

class ActionType(Enum):
    """Typy akcji gracza"""
    MOVE = "move"
    EXAMINE = "examine"
    TALK = "talk"
    COMBAT = "combat"
    INTERACT = "interact"
    CHOICE = "choice"

class AdaptiveGameMaster:
    """
    Inteligentny Game Master który:
    - Dynamicznie zmienia styl narracji
    - Tworzy własne NPC i nazwy
    - Używa Wiki jako fundamentu kanonu
    - Buduje logiczną, niepowtarzalną fabułę
    """
    
    def __init__(self, model_name: str = "llama3.1:8b"):
        self.model_name = model_name
        self.client = ollama.Client()
        self.scraper = WikiScraper()
        
        # Cache dla danych z Wiki
        self.wiki_cache = {}
        
        # Stan fabularny sesji (każda sesja ma swój)
        self.story_states = {}
        
        self.system_prompt = """Jesteś kreatywnym Mistrzem Gry w uniwersum {universe}.

ZASADY ABSOLUTNE:
1. KANON z Wiki: planety, rasy, technologie, historia - NIGDY nie zmieniaj
2. MOŻESZ tworzyć: 
   - Nowe NPC (imiona, osobowości, historie)
   - Nazwy statków, tawern, organizacji
   - Drobne przedmioty i lokacje w istniejących miejscach
3. Buduj LOGICZNE konsekwencje - każda akcja ma wpływ
4. Twórz NIEPOWTARZALNĄ fabułę - unikaj klisz
5. ZMIENIAJ dynamikę - czasem daj wolność, czasem wybory, czasem akcję

STYL NARRACJI:
- Opisuj używając wszystkich zmysłów
- NPC mają własne cele, nie są tylko tłem
- Wydarzenia są ze sobą powiązane
- Buduj napięcie stopniowo
- Pamiętaj o konsekwencjach poprzednich decyzji"""
    
    def start_session(self, character: Dict, universe: str = None) -> Dict:
        """Rozpoczyna nową sesję z unikalną fabułą"""
        
        universe = universe or character.get('universe', 'star_wars')
        session_id = character.get('session_id', 'default')
        
        # Inicjalizuj stan fabularny dla tej sesji
        self.story_states[session_id] = {
            'current_beat': StoryBeat.INTRO,
            'tension_level': 0,
            'player_agency': 8,  # Start z dużą wolnością
            'active_npcs': {},
            'story_threads': [],
            'consequences': {},
            'visited_locations': [],
            'items_collected': [],
            'relationships': {},  # NPC -> stosunek do gracza
            'main_quest': None,
            'side_quests': []
        }
        
        # Pobierz dane o rasie postaci z Wiki
        race_data = None
        if character.get('race'):
            race_data = self._get_wiki_data(character['race'], universe)
        
        # Wygeneruj unikalny początek bazując na postaci
        intro_context = self._generate_unique_intro(character, race_data, universe)
        
        return {
            'message': intro_context['message'],
            'type': 'narration',
            'timestamp': datetime.now().isoformat(),
            'location': intro_context['location'],
            'story_hook': intro_context.get('hook'),
            'session_id': session_id
        }
    
    def process_action(self, action: str, context: Dict) -> Dict:
        """Główna metoda przetwarzająca akcje gracza"""
        
        session_id = context.get('session_id', 'default')
        universe = context.get('universe', 'star_wars')
        
        # Pobierz stan fabularny
        story_state = self.story_states.get(session_id, self._init_story_state())
        
        # 1. Parsuj intencję gracza
        action_type, entities = self._parse_action(action)
        
        # 2. Pobierz dane z Wiki dla znalezionych encji
        wiki_data = self._fetch_wiki_data_for_entities(entities, universe)
        
        # 3. Określ styl narracji dla tej akcji
        narrative_style = self._determine_narrative_style(action_type, story_state, context)
        
        # 4. Aktualizuj stan fabularny
        self._update_story_state(action, action_type, story_state)
        
        # 5. Generuj odpowiedź w odpowiednim stylu
        response = self._generate_adaptive_response(
            action=action,
            action_type=action_type,
            narrative_style=narrative_style,
            wiki_data=wiki_data,
            story_state=story_state,
            context=context
        )
        
        # 6. Zapisz zmiany w stanie
        self.story_states[session_id] = story_state
        
        return response
    
    def _generate_unique_intro(self, character: Dict, race_data: Dict, universe: str) -> Dict:
        """Generuje unikalny początek sesji"""
        
        # Wybierz losową lokację startową (kanoniczną)
        starting_locations = self._get_canon_starting_locations(universe)
        location = random.choice(starting_locations) if starting_locations else "Unknown Location"
        
        # Pobierz dane o lokacji
        location_data = self._get_wiki_data(location, universe)
        
        # Stwórz hook fabularny
        story_hooks = [
            f"Docierają do ciebie niepokojące plotki o dziwnych zdarzeniach w {location}.",
            f"Otrzymujesz tajemniczą wiadomość wzywającą cię do {location}.",
            f"Twój statek musi awaryjnie lądować w {location}.",
            f"Szukasz kogoś, kto podobno ostatnio był widziany w {location}.",
            f"Zlecenie które przyjąłeś prowadzi cię do {location}."
        ]
        
        hook = random.choice(story_hooks)
        
        # Stwórz pierwszego NPC
        npc = self._create_npc(universe, "informator")
        
        prompt = f"""Uniwersum: {universe}
Postać gracza: {character.get('name')} - {character.get('race')} {character.get('class_type')}
Lokacja: {location}
Dane o lokacji z Wiki: {location_data.get('description', 'Brak danych')[:300] if location_data else 'Brak'}
Hook fabularny: {hook}
NPC w pobliżu: {npc['name']} ({npc['race']}) - {npc['personality']}

Stwórz atmosferyczne wprowadzenie do sesji (3-4 zdania). Opisz gdzie jest gracz i co widzi/czuje.
NIE rozpoczynaj akcji, tylko ustaw scenę."""

        intro = self._generate_llm_response(prompt, universe)
        
        return {
            'message': intro,
            'location': location,
            'hook': hook,
            'first_npc': npc
        }
    
    def _parse_action(self, action: str) -> Tuple[ActionType, List[str]]:
        """Parsuje akcję gracza na typ i encje"""
        
        action_lower = action.lower()
        
        # Określ typ akcji
        if re.search(r'\b[ABC]\)|wybier|opcj', action):
            action_type = ActionType.CHOICE
        elif re.search(r'\b(idź|iść|przejdź|wejdź|udaj|rusz|bieg|leć)\b', action_lower):
            action_type = ActionType.MOVE
        elif re.search(r'\b(patrz|zobacz|rozglą|obserw|sprawdź|zbadaj)\b', action_lower):
            action_type = ActionType.EXAMINE
        elif re.search(r'\b(mów|powiedz|pytaj|rozmaw|gadaj|zapytaj)\b', action_lower):
            action_type = ActionType.TALK
        elif re.search(r'\b(walcz|atakuj|bij|strzel|broń)\b', action_lower):
            action_type = ActionType.COMBAT
        elif re.search(r'\b(weź|podnieś|użyj|kup|sprzedaj|otwórz)\b', action_lower):
            action_type = ActionType.INTERACT
        else:
            action_type = ActionType.INTERACT
        
        # Wyciągnij encje (nazwy własne)
        entities = []
        
        # Wszystkie słowa z wielkiej litery
        entities.extend(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', action))
        
        # Specyficzne terminy
        special_terms = re.findall(r'\b(kantyn\w*|tawern\w*|port\w*|statek|miecz|blaster)\b', action_lower)
        entities.extend(special_terms)
        
        return action_type, list(set(entities))
    
    def _determine_narrative_style(self, action_type: ActionType, story_state: Dict, context: Dict) -> NarrativeStyle:
        """Inteligentnie wybiera styl narracji"""
        
        tension = story_state['tension_level']
        beat = story_state['current_beat']
        history = context.get('history', [])
        
        # Jeśli gracz wybrał opcję - kontynuuj wybory
        if action_type == ActionType.CHOICE:
            return NarrativeStyle.CHOICES
        
        # Analiza ostatnich akcji
        recent_actions = history[-5:] if len(history) >= 5 else history
        action_types = [a.get('type') for a in recent_actions]
        
        # Jeśli gracz był pasywny - zaproponuj wybory
        if action_types.count('observation') > 3:
            story_state['player_agency'] = 5
            return NarrativeStyle.CHOICES
        
        # Podczas walki - kinematyczne
        if action_type == ActionType.COMBAT or tension > 8:
            return NarrativeStyle.CINEMATIC
        
        # Podczas rozmowy - kierowane
        if action_type == ActionType.TALK:
            return NarrativeStyle.GUIDED
        
        # Domyślnie - otwarta eksploracja
        return NarrativeStyle.OPEN_WORLD
    
    def _generate_adaptive_response(
        self, 
        action: str,
        action_type: ActionType,
        narrative_style: NarrativeStyle,
        wiki_data: Dict,
        story_state: Dict,
        context: Dict
    ) -> Dict:
        """Generuje odpowiedź w zależności od stylu narracji"""
        
        universe = context.get('universe', 'star_wars')
        
        # Formatuj kontekst Wiki
        wiki_context = self._format_wiki_context(wiki_data)
        
        # Różne generatory dla różnych stylów
        if narrative_style == NarrativeStyle.CHOICES:
            return self._generate_choice_response(action, wiki_context, story_state, universe)
        elif narrative_style == NarrativeStyle.CINEMATIC:
            return self._generate_cinematic_response(action, wiki_context, story_state, universe)
        elif narrative_style == NarrativeStyle.GUIDED:
            return self._generate_guided_response(action, wiki_context, story_state, universe)
        else:
            return self._generate_open_response(action, wiki_context, story_state, universe)
    
    def _generate_choice_response(self, action: str, wiki_context: str, story_state: Dict, universe: str) -> Dict:
        """Generuje odpowiedź z wyborami"""
        
        # Sprawdź czy to odpowiedź na wybór
        choice_match = re.match(r'^([ABC])\)', action.strip())
        if choice_match:
            choice = choice_match.group(1)
            return self._process_choice(choice, story_state, universe)
        
        # Generuj nowe wybory
        npc = self._get_or_create_local_npc(story_state, universe)
        
        prompt = f"""Uniwersum: {universe}

DANE Z WIKI:
{wiki_context}

STAN FABULARNY:
- Napięcie: {story_state['tension_level']}/10
- Aktywne wątki: {story_state.get('story_threads', [])}
- NPC w pobliżu: {npc['name']} - {npc['personality']}

Akcja gracza: {action}

Stwórz interesującą sytuację z 3 różnymi opcjami.
Każda opcja powinna prowadzić w innym kierunku fabularnym.

Format odpowiedzi:
[Opis sytuacji - 2-3 zdania]

A) [Opcja bezpieczna/dyplomatyczna]
B) [Opcja ryzykowna/akcji]
C) [Opcja kreatywna/nieoczywista]"""

        response = self._generate_llm_response(prompt, universe)
        
        return {
            'message': response,
            'type': 'choice',
            'narrative_style': 'choices',
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_cinematic_response(self, action: str, wiki_context: str, story_state: Dict, universe: str) -> Dict:
        """Generuje kinematyczną scenę akcji"""
        
        # Zwiększ napięcie
        story_state['tension_level'] = min(10, story_state['tension_level'] + 2)
        
        prompt = f"""Uniwersum: {universe}

DANE Z WIKI (użyj do szczegółów):
{wiki_context}

NAPIĘCIE: WYSOKIE ({story_state['tension_level']}/10)
Akcja gracza: {action}

Stwórz DYNAMICZNĄ, kinematyczną scenę:
1. Coś nieoczekiwanego się dzieje
2. Użyj kanonicznych elementów z Wiki
3. Wprowadź nowego NPC jeśli pasuje
4. Zakończ cliffhangerem

Styl: Akcja, napięcie, wszystkie zmysły. 3-5 zdań."""

        response = self._generate_llm_response(prompt, universe)
        
        # Dodaj efekty dźwiękowe/wizualne
        effects = self._add_scene_effects(action)
        
        return {
            'message': response,
            'type': 'cinematic',
            'narrative_style': 'cinematic',
            'effects': effects,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_open_response(self, action: str, wiki_context: str, story_state: Dict, universe: str) -> Dict:
        """Generuje otwartą odpowiedź z pełną wolnością"""
        
        prompt = f"""Uniwersum: {universe}

DANE Z WIKI:
{wiki_context}

EKSPLORACJA:
- Odwiedzone miejsca: {story_state.get('visited_locations', [])}
- Znalezione przedmioty: {story_state.get('items_collected', [])}

Akcja gracza: {action}

Opisz rezultat dając graczowi PEŁNĄ swobodę.
Możesz:
- Stworzyć nowego NPC
- Odkryć nowe miejsce (w ramach kanonu)
- Znaleźć przedmiot
- Rozpocząć nowy wątek fabularny

Pamiętaj o konsekwencjach poprzednich akcji."""

        response = self._generate_llm_response(prompt, universe)
        
        return {
            'message': response,
            'type': 'exploration',
            'narrative_style': 'open_world',
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_guided_response(self, action: str, wiki_context: str, story_state: Dict, universe: str) -> Dict:
        """Generuje delikatnie kierowaną odpowiedź"""
        
        # Sugeruj kierunek bez wymuszania
        hints = self._generate_story_hints(story_state)
        
        prompt = f"""Uniwersum: {universe}

DANE Z WIKI:
{wiki_context}

WĄTKI FABULARNE: {story_state.get('story_threads', [])}
WSKAZÓWKI DLA GRACZA: {hints}

Akcja gracza: {action}

Opisz rezultat i DELIKATNIE zasugeruj możliwe kierunki akcji.
Nie wymuszaj, tylko pokaż możliwości."""

        response = self._generate_llm_response(prompt, universe)
        
        return {
            'message': response,
            'type': 'guided',
            'narrative_style': 'guided',
            'hints': hints,
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_npc(self, universe: str, role: str = None) -> Dict:
        """Tworzy unikatowego NPC"""
        
        # Pobierz kanoniczne rasy
        races = self._get_canon_races(universe)
        
        # Generuj imię
        name = self._generate_npc_name(universe)
        
        # Generuj osobowość i motywację
        personalities = [
            "nerwowy i podejrzliwy",
            "pewny siebie i arogancki",
            "przyjazny ale przebiegły",
            "zmęczony i cyniczny",
            "entuzjastyczny i naiwny",
            "tajemniczy i enigmatyczny",
            "brutalny i bezpośredni",
            "uprzejmy ale zdystansowany"
        ]
        
        motivations = [
            "szuka łatwego zarobku",
            "ukrywa mroczną tajemnicę",
            "ma dług do spłacenia",
            "szuka zemsty",
            "próbuje chronić kogoś bliskiego",
            "ma ważne informacje",
            "potrzebuje pomocy",
            "realizuje czyjś zlecenie"
        ]
        
        occupations = {
            'star_wars': ['przemytnik', 'pilot', 'mechanik', 'handlarz', 'łowca nagród', 
                         'informator', 'barman', 'technik', 'medyk', 'najemnik'],
            'lotr': ['karczmarz', 'kupiec', 'strażnik', 'zwiadowca', 'kowal', 'łowca'],
            'default': ['mieszkaniec', 'handlarz', 'strażnik']
        }
        
        npc = {
            'name': name,
            'race': random.choice(races) if races else 'Human',
            'occupation': role or random.choice(occupations.get(universe, occupations['default'])),
            'personality': random.choice(personalities),
            'motivation': random.choice(motivations),
            'first_meeting': True,
            'relationship': 0  # -10 do +10
        }
        
        return npc
    
    def _generate_npc_name(self, universe: str) -> str:
        """Generuje imię pasujące do uniwersum"""
        
        if universe == 'star_wars':
            prefixes = ["Zar", "Kor", "Jax", "Ven", "Dar", "Mal", "Tor", "Ral", "Xan", "Bren"]
            suffixes = ["ek", "an", "is", "on", "ax", "us", "ara", "ith", "el", "inn"]
            return f"{random.choice(prefixes)}{random.choice(suffixes)}"
        elif universe == 'lotr':
            prefixes = ["Brom", "Gar", "Thal", "Dun", "Mor", "Grim", "Bar"]
            suffixes = ["dir", "mond", "wick", "stone", "hill", "brook"]
            return f"{random.choice(prefixes)}{random.choice(suffixes)}"
        else:
            return f"NPC_{random.randint(100, 999)}"
    
    def _get_canon_races(self, universe: str) -> List[str]:
        """Pobiera listę kanonicznych ras"""
        
        cache_key = f"{universe}_races"
        if cache_key in self.wiki_cache:
            return self.wiki_cache[cache_key]
        
        # Tu normalnie pobierałbyś z Wiki
        # Tymczasowo zwracam przykładowe
        races = {
            'star_wars': ['Human', 'Twi\'lek', 'Rodian', 'Zabrak', 'Duros', 'Mon Calamari', 
                         'Bothan', 'Sullustan', 'Wookiee', 'Trandoshan'],
            'lotr': ['Human', 'Elf', 'Dwarf', 'Hobbit'],
            'default': ['Human']
        }
        
        result = races.get(universe, races['default'])
        self.wiki_cache[cache_key] = result
        return result
    
    def _get_canon_starting_locations(self, universe: str) -> List[str]:
        """Zwraca listę kanonicznych lokacji startowych"""
        
        locations = {
            'star_wars': ['Tatooine', 'Coruscant', 'Naboo', 'Corellia', 'Nar Shaddaa'],
            'lotr': ['Shire', 'Bree', 'Rivendell', 'Gondor'],
            'default': ['Starting City']
        }
        
        return locations.get(universe, locations['default'])
    
    def _update_story_state(self, action: str, action_type: ActionType, story_state: Dict):
        """Aktualizuje stan fabularny na podstawie akcji"""
        
        # Zwiększ napięcie przy walce
        if action_type == ActionType.COMBAT:
            story_state['tension_level'] = min(10, story_state['tension_level'] + 2)
        
        # Zmniejsz napięcie przy eksploracji
        elif action_type == ActionType.EXAMINE:
            story_state['tension_level'] = max(0, story_state['tension_level'] - 1)
        
        # Progresja fabuły
        if story_state['tension_level'] > 7:
            if story_state['current_beat'] != StoryBeat.CLIMAX:
                story_state['current_beat'] = StoryBeat.CLIMAX
        elif story_state['tension_level'] > 4:
            story_state['current_beat'] = StoryBeat.CONFLICT
        elif story_state['tension_level'] > 2:
            story_state['current_beat'] = StoryBeat.BUILD_UP
        
        # Zapisz konsekwencje drastycznych akcji
        if any(word in action.lower() for word in ['zabij', 'zniszcz', 'ukradnij']):
            story_state['consequences']['violent_action'] = True
            story_state['tension_level'] = min(10, story_state['tension_level'] + 3)
    
    def _fetch_wiki_data_for_entities(self, entities: List[str], universe: str) -> Dict:
        """Pobiera dane z Wiki dla znalezionych encji"""
        
        wiki_data = {}
        
        for entity in entities[:5]:  # Max 5 encji żeby nie przeciążać
            data = self._get_wiki_data(entity, universe)
            if data:
                wiki_data[entity] = data
        
        return wiki_data
    
    def _get_wiki_data(self, entity: str, universe: str) -> Optional[Dict]:
        """Pobiera dane z cache lub Wiki"""
        
        cache_key = f"{universe}:{entity.lower()}"
        
        if cache_key in self.wiki_cache:
            return self.wiki_cache[cache_key]
        
        try:
            url = self.scraper.search_character(entity, universe)
            if url:
                data = self.scraper.scrape_character_data(url)
                if data:
                    self.wiki_cache[cache_key] = data
                    return data
        except Exception as e:
            print(f"Wiki error for {entity}: {e}")
        
        return None
    
    def _format_wiki_context(self, wiki_data: Dict) -> str:
        """Formatuje dane z Wiki jako kontekst"""
        
        if not wiki_data:
            return "Brak danych z Wiki dla tej akcji."
        
        context_parts = []
        for entity, data in wiki_data.items():
            part = f"[{entity}]: "
            if data.get('description'):
                part += data['description'][:200]
            context_parts.append(part)
        
        return "\n".join(context_parts)
    
    def _get_or_create_local_npc(self, story_state: Dict, universe: str) -> Dict:
        """Pobiera lub tworzy NPC dla obecnej lokacji"""
        
        active_npcs = story_state.get('active_npcs', {})
        
        # Jeśli są już NPC, może użyj istniejącego
        if active_npcs and random.random() > 0.6:
            return random.choice(list(active_npcs.values()))
        
        # Stwórz nowego
        npc = self._create_npc(universe)
        npc_id = f"npc_{len(active_npcs)}"
        story_state['active_npcs'][npc_id] = npc
        
        return npc
    
    def _process_choice(self, choice: str, story_state: Dict, universe: str) -> Dict:
        """Przetwarza wybór gracza"""
        
        # Tu powinna być logika reagująca na konkretny wybór
        # Na razie zwracamy ogólną odpowiedź
        
        responses = {
            'A': "Wybierasz ostrożne podejście. ",
            'B': "Decydujesz się na bezpośrednią akcję. ",
            'C': "Wybierasz niekonwencjonalne rozwiązanie. "
        }
        
        base_response = responses.get(choice, "Podejmujesz decyzję. ")
        
        # Modyfikuj stan na podstawie wyboru
        if choice == 'B':
            story_state['tension_level'] = min(10, story_state['tension_level'] + 1)
        
        return {
            'message': base_response + "Konsekwencje twojego wyboru szybko stają się widoczne...",
            'type': 'consequence',
            'choice_made': choice,
            'timestamp': datetime.now().isoformat()
        }
    
    def _add_scene_effects(self, action: str) -> List[str]:
        """Dodaje efekty do sceny kinematycznej"""
        
        effects = []
        
        if 'strzel' in action.lower() or 'blaster' in action.lower():
            effects.append("sound:blaster_fire")
            effects.append("visual:laser_flash")
        elif 'miecz' in action.lower():
            effects.append("sound:lightsaber_hum")
            effects.append("visual:saber_glow")
        elif 'wybuch' in action.lower():
            effects.append("sound:explosion")
            effects.append("visual:screen_shake")
        
        return effects
    
    def _generate_story_hints(self, story_state: Dict) -> List[str]:
        """Generuje subtelne wskazówki fabularne"""
        
        hints = []
        
        if story_state['tension_level'] < 3:
            hints.append("Okolica wydaje się spokojna, może za spokojna...")
        elif story_state['tension_level'] > 7:
            hints.append("Napięcie jest wyczuwalne w powietrzu.")
        
        if not story_state.get('visited_locations'):
            hints.append("Warto rozejrzeć się po okolicy.")
        
        return hints
    
    # Na końcu pliku - POPRAW TO (przenieś do klasy):
    def generate_dice_roll(self, dice_type: str = 'd20') -> Dict:
        """Generuje rzut kością"""
        dice_values = {
            'd4': 4, 'd6': 6, 'd8': 8, 'd10': 10,
            'd12': 12, 'd20': 20, 'd100': 100
        }
        
        max_value = dice_values.get(dice_type, 20)
        roll = random.randint(1, max_value)
        
        critical = None
        if dice_type == 'd20':
            if roll == 20:
                critical = 'success'
            elif roll == 1:
                critical = 'failure'
        
        return {
            'dice': dice_type,
            'result': roll,
            'critical': critical,
            'message': f"Rzut {dice_type}: {roll}" + 
                      (f" - Krytyczny {'sukces' if critical == 'success' else 'porażka'}!" if critical else "")
        }
    
    def _init_story_state(self) -> Dict:
        """Inicjalizuje nowy stan fabularny"""
        
        return {
            'current_beat': StoryBeat.INTRO,
            'tension_level': 0,
            'player_agency': 8,
            'active_npcs': {},
            'story_threads': [],
            'consequences': {},
            'visited_locations': [],
            'items_collected': [],
            'relationships': {}
        }
    
    def _generate_llm_response(self, prompt: str, universe: str) -> str:
        """Generuje odpowiedź używając Ollama"""
        
        if not self._check_ollama_connection():
            return "Kontynuujesz swoją przygodę..."
        
        # Dodaj uniwersum do promptu systemowego
        full_prompt = self.system_prompt.format(universe=universe) + "\n\n" + prompt
        
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=full_prompt,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'max_tokens': 400
                }
            )
            return response['response'].strip()
        except Exception as e:
            print(f"Ollama error: {e}")
            return "Akcja wykonana pomyślnie."
        
    
    def _check_ollama_connection(self) -> bool:
        """Sprawdza połączenie z Ollama"""
        try:
            self.client.list()
            return True
        except:
            return False
        
        # Dodaj tę metodę do klasy AdaptiveGameMaster w adaptive_game_master.py
        
    
