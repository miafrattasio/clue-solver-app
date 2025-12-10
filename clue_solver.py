import itertools
import json

# --- CARD DEFINITIONS ---
ORIGINAL_CARDS = {
    "Suspect": ["Miss Scarlett", "Colonel Mustard", "Mrs. White", "Reverend Green", "Mrs. Peacock", "Professor Plum"],
    "Weapon": ["Candlestick", "Dagger", "Lead Pipe", "Revolver", "Rope", "Wrench"],
    "Room": ["Kitchen", "Ballroom", "Conservatory", "Dining Room", "Billiard Room", "Library", "Lounge", "Hall", "Study"]
}

# Master Detective Clue (10 suspects, 8 weapons, 12 rooms = 30 cards total)
MASTER_DETECTIVE_CARDS = {
    "Suspect": [
        "Colonel Mustard", "Professor Plum", "Mrs. Peacock", "Mr. Green", 
        "Miss Scarlet", "Mrs. White", "Miss Peach", "Monsieur Brunette", 
        "Madame Rose", "Sergeant Gray"
    ],
    "Weapon": ["Candlestick", "Knife", "Lead Pipe", "Revolver", "Rope", "Wrench", "Poison", "Horseshoe"],
    "Room": [
        "Carriage House", "Trophy Room", "Kitchen", "Dining Room", "Drawing Room", 
        "Gazebo", "Courtyard", "Fountain", "Library", "Billiard Room", 
        "Studio", "Conservatory"
    ]
}

# --- KNOWLEDGE CONSTANTS (USING NUMBERS FOR COMPARISON LOGIC) ---
UNKNOWN_NUM = 0
NO_CARD_NUM = 1
HAS_CARD_NUM = 2
IN_ENVELOPE_NUM = 3

# --- KNOWLEDGE SYMBOLS (FOR DISPLAY) ---
KNOWLEDGE_SYMBOLS = {
    UNKNOWN_NUM: '',      
    NO_CARD_NUM: '✗',    
    HAS_CARD_NUM: '✓',   
    IN_ENVELOPE_NUM: '⭐' 
}

HAS_CARD = HAS_CARD_NUM
NO_CARD = NO_CARD_NUM


class ClueDeductionEngine:
    def __init__(self, players, card_sets, user_name):
        self.players = [p.lower() for p in players]
        self.user_name = user_name.lower()
        self.card_sets = card_sets
        self.all_cards = list(itertools.chain.from_iterable(card_sets.values()))
        self.num_cards = len(self.all_cards)
        self.num_players = len(self.players)
        
        self.knowledge = {
            card: {player: UNKNOWN_NUM for player in self.players + ['Envelope']}
            for card in self.all_cards
        }
        
        self.player_card_counts = {player: 0 for player in self.players}
        
        # NEW: Tracker for cards the user showed to opponents
        # Format: {opponent_name: [list of cards shown]}
        self.cards_shown_to_player = {
            player: [] for player in self.players if player != self.user_name
        }
        
        # Calculate base hand size
        cards_per_player = self.num_cards // self.num_players
        remainder = self.num_cards % self.num_players
        for i, player in enumerate(self.players):
            self.player_card_counts[player] = cards_per_player + (1 if i < remainder else 0)

        self.log = []

    # --- Serialization Methods remain the same ---
    def to_json(self):
        data = self.__dict__.copy()
        data['card_sets_key'] = 'MASTER_DETECTIVE_CARDS' if self.card_sets == MASTER_DETECTIVE_CARDS else 'ORIGINAL_CARDS'
        del data['card_sets']
        return data

    @classmethod
    def from_json(cls, data):
        card_sets_key = data.pop('card_sets_key')
        card_sets = MASTER_DETECTIVE_CARDS if card_sets_key == 'MASTER_DETECTIVE_CARDS' else ORIGINAL_CARDS
        
        instance = cls.__new__(cls) 
        instance.card_sets = card_sets
        instance.__dict__.update(data)
        return instance

    # --- Deduction Logic remains the same, except for new tracking in _update_knowledge ---
    
    def _add_log(self, message):
        self.log.append(message)

    def _update_knowledge(self, card, location, status):
        """Helper to safely update the knowledge matrix and run general deductions."""
        if self.knowledge[card][location] < status:
            self.knowledge[card][location] = status
            
            if status == HAS_CARD_NUM:
                self._add_log(f"-> Deduction: **{location.capitalize()}** must **HAVE** **{card}**")
                for other_location in self.players + ['Envelope']:
                    if other_location != location:
                        self._update_knowledge(card, other_location, NO_CARD_NUM)
                self.check_player_hand_complete(location)
            
            if status == IN_ENVELOPE_NUM:
                self._add_log(f"-> Deduction: **{card}** is **IN THE ENVELOPE!**")
                for other_player in self.players:
                    self._update_knowledge(card, other_player, NO_CARD_NUM)
            
            self.check_for_solution_card(card)
            
    # --- Other methods (check_for_solution_card, check_player_hand_complete, input_player_hand, log_suggestion) remain the same ---
    
    def input_player_hand(self, card_list):
        """Initial input of the user's hand."""
        self.log = []
        for card in card_list:
            if card not in self.all_cards:
                self._add_log(f"Warning: Card '{card}' not recognized in game version.")
                continue
            self._update_knowledge(card, self.user_name, HAS_CARD_NUM)
        
        self._add_log(f"Initial hand of **{sum(1 for card in card_list if card in self.all_cards)} cards** logged for **{self.user_name.capitalize()}**.")

    def log_suggestion(self, suggester, suspect, weapon, room, refuter, was_card_shown):
        """Logs a suggestion and runs the smart deduction logic."""
        self.log = []
        suggester = suggester.lower()
        refuter = refuter.lower()
        suggestion = [suspect, weapon, room]
        
        self._add_log(f"--- Turn Log: **{suggester.capitalize()}** suggested **{suspect}**, **{weapon}**, **{room}** ---")
        
        if was_card_shown and refuter != 'none':
            num_no_card = sum(1 for card in suggestion if self.knowledge[card][refuter] == NO_CARD_NUM)
            
            if num_no_card == 2:
                card_must_be = next(c for c in suggestion if self.knowledge[c][refuter] != NO_CARD_NUM)
                self._add_log(f"*** SMART DEDUCTION: **{refuter.capitalize()}** is KNOWN NOT to have 2 of 3 cards. They **MUST** have shown **{card_must_be}**! ***")
                self._update_knowledge(card_must_be, refuter, HAS_CARD_NUM)
            elif num_no_card == 1:
                self._add_log(f"-> Partial Deduction: **{refuter.capitalize()}** has one of the two remaining possible cards.")
            elif num_no_card == 0:
                 self._add_log(f"-> Partial Deduction: **{refuter.capitalize()}** has one of the three possible cards.")
        
    def check_for_solution_card(self, card):
        # Implementation remains the same
        if self.knowledge[card]['Envelope'] == UNKNOWN_NUM:
            no_card_count = sum(1 for player in self.players if self.knowledge[card][player] == NO_CARD_NUM)
            if no_card_count == self.num_players:
                self._update_knowledge(card, 'Envelope', IN_ENVELOPE_NUM)
        
        unknown_locations = []
        for location in self.players:
            if self.knowledge[card][location] == UNKNOWN_NUM:
                unknown_locations.append(location)

        if len(unknown_locations) == 1:
            player = unknown_locations[0]
            other_locations = [p for p in self.players if p != player]
            if all(self.knowledge[card][loc] == NO_CARD_NUM for loc in other_locations) and self.knowledge[card]['Envelope'] == NO_CARD_NUM:
                 self._update_knowledge(card, player, HAS_CARD_NUM)

    def check_player_hand_complete(self, player):
        # Implementation remains the same
        if player == 'Envelope':
            return
            
        cards_known = sum(1 for card in self.all_cards if self.knowledge[card][player] == HAS_CARD_NUM)
        
        if cards_known == self.player_card_counts[player]:
            self._add_log(f"*** SMART DEDUCTION: **{player.capitalize()}'s** hand is COMPLETE! (All {self.player_card_counts[player]} cards are known) ***")
            for card in self.all_cards:
                if self.knowledge[card][player] == UNKNOWN_NUM:
                    self._update_knowledge(card, player, NO_CARD_NUM)
                    
    def get_status_summary(self):
        """Returns the solution and the deduction table for display."""
        solution = {}
        for card_type, cards in self.card_sets.items():
            for card in cards:
                if self.knowledge[card]['Envelope'] == IN_ENVELOPE_NUM:
                    solution[card_type] = card
        
        # --- Create Deduction Matrix with SYMBOLS ---
        header = ["Card"] + [p.capitalize() for p in self.players] + ["Envelope"]
        table = []

        for card in self.all_cards:
            row = [card]
            for player in self.players + ['Envelope']:
                numerical_status = self.knowledge[card][player]
                row.append(KNOWLEDGE_SYMBOLS.get(numerical_status, ''))
            table.append(row)
            
        # --- Create Possibility Summary ---
        possibilities = {}
        for card_type in self.card_sets:
            possible_solutions = [
                card for card in self.card_sets[card_type] 
                if self.knowledge[card]['Envelope'] not in (NO_CARD_NUM, IN_ENVELOPE_NUM)
            ]
            possibilities[card_type] = possible_solutions

        # NEW: Return the card show history
        return solution, header, table, possibilities, self.cards_shown_to_player