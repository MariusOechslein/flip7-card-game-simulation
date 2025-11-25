"""TODO: Use Pydantic! TODO: Use Logging library! TODO: Use Debugger for errors!"""

import random
from collections import deque # For next player rotations
from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing import List
from uuid import uuid4

card_decks = {
    "normal_cards_only": [
        *["0"] * 1,
        *["1"] * 1,
        *["2"] * 2,
        *["3"] * 3,
        *["4"] * 4,
        *["5"] * 5,
        *["6"] * 6,
        *["7"] * 7,
        *["8"] * 8,
        *["9"] * 9,
        *["10"] * 10,
        *["11"] * 11,
        *["12"] * 12,
    ],
    "full_deck": [
        *["0"] * 1,
        *["1"] * 1,
        *["2"] * 2,
        *["3"] * 3,
        *["4"] * 4,
        *["5"] * 5,
        *["6"] * 6,
        *["7"] * 7,
        *["8"] * 8,
        *["9"] * 9,
        *["10"] * 10,
        *["11"] * 11,
        *["12"] * 12,
        "x2", "+2", "+4", "+6", "+8", "+10",
        *["freeze"] * 3,
        *["second_chance"] * 3,
        *["draw_3"] * 3,
    ],
}

class Game(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True) # Needed for random.Random type

    finished: bool = Field(default=False, description="Boolean indicating if the game is finished.")
    players: deque = Field(..., description="Deque of Player objects representing the players in the game and turn order.")
    deck_remaining: List[str] = Field(..., description="List of strings representing the remaining cards in the deck.")
    seed: int = Field(default_factory=lambda: random.randint(0, 1_000_000), description="Random seed for the game.")
    rng: random.Random = Field(default=None, description="Instance-specific random generator.")
    
    def model_post_init(self, __context):
        """Create instance-specific random generator.
        Note: Pydantic automatically runs this after initialization."""
        self.rng = random.Random(self.seed)

    @field_validator("players", mode="before")
    @classmethod
    def check_players(cls, v):
        if not isinstance(v, deque):
            raise ValueError("players must be a deque")
        if len(v) < 1:
            raise ValueError("must have at least 1 player")
        return v

    @field_validator("deck_remaining", mode="before")
    @classmethod
    def check_deck_remaining(cls, v):
        if len(v) > len(card_decks["full_deck"]):
            raise ValueError("deck_remaining longer than full deck")
        for card in v:
            if not isinstance(card, str):
                raise ValueError("Cards must be strings")
            if card not in card_decks["full_deck"]:
                raise ValueError("Card not valid in deck_remaining:", card)
        return v

    def next(self):
        if self.finished:
            print("Game is over.")
            for i, player in enumerate(self.players):
                print("Player", str(i), "score:", player.count_score())
            return

        next_player = self.next_player()
        next_player.play(game=self)

    def next_player(self):
        next_player = self.players[0]
        self.players.rotate(-1)
        return next_player

    def draw_card(self):
        card = self.rng.choice(self.deck_remaining)
        self.deck_remaining.remove(card)
        return card

    def apply_draw_3(self, to_player_id: str):
        for player in self.players:
            if player.id == to_player_id:
                player.in_draw_3 = True
                player.play(game=self)
                player.play(game=self)
                player.play(game=self)
                player.in_draw_3 = False
                return
        raise ValueError("Error: Player with id", to_player_id, "not found for draw 3 card.")

    def game_summary(self):
        print("Player scores:")
        for i, player in enumerate(self.players):
            print("Player", str(i), "score:", player.count_score(), "hand:", player.hand.normal, "bonus:", player.hand.bonus, "special_cards_log:", player.hand.special_cards_log, "busted:", player.busted)



class Hand(BaseModel):
    normal: List[str] = Field(default=[], description="List of normal cards in hand.")
    bonus: List[str] = Field(default=[], description="List of bonus cards in hand.")
    special_cards_log: List[str] = Field(default=[], description="List of special cards in hand.")

    @field_validator("normal", mode="before")
    def check_normal(cls, v):
        for card in v:
            if not card in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]:
                raise ValueError("Normal Cards not valid")
        return v

    @field_validator("bonus", mode="before")
    def check_bonus(cls, v):
        for card in v:
            if not card in ["x2", "+2", "+4", "+6", "+8", "+10"]:
                raise ValueError("Bonus Cards not valid")
        return v

    @field_validator("special_cards_log", mode="before")
    def check_special_cards_log(cls, v):
        for card in v:
            if not card in ["freeze", "second_chance", "draw_3"]:
                raise ValueError("Special Cards not valid")
        return v


class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the player.")
    done: bool = Field(default=False, description="Boolean indicating if the player is done playing this round.")
    busted: bool = Field(default=False, description="Boolean indicating if the player has busted this round.")
    in_draw_3: bool = Field(default=False, description="Boolean indicating if the player is currently affected by a 'draw 3' card.")
    hand: Hand = Field(default=Hand(), description="Player's hand containing normal and bonus cards.")
    second_chance: bool = Field(default=False, description="Boolean indicating if the player has a second chance special card to use against busting.")
    name: str = Field(default="Unknown Player", description="Name of the player.")

    def play(self, game: Game):
        """ Executes the player's turn in the game."""
        if self.done or self.busted:
            return

        # TODO: Implement logging strategy instead of print statements
        print("Player:", self.name, "turn.")

        if not self.in_draw_3 and self.decide_draw() == False:
            self.done = True
            return

        drawn_card = game.draw_card()
        print("Card drawn:", drawn_card)
        print("Hand:", self.hand.normal)

        if drawn_card in ["0","1","2","3","4","5","6","7","8","9","10","11","12"]:
            self.hand.normal.append(drawn_card)
        elif drawn_card in ["x2", "+2", "+4", "+6", "+8", "+10"]:
            self.hand.bonus.append(drawn_card)
        elif drawn_card == "freeze" or drawn_card == "second_chance" or drawn_card == "draw_3":
            self.hand.special_cards_log.append(drawn_card)

            if drawn_card == "second_chance":
                self.second_chance = True
            if drawn_card == "freeze":
                self.decide_freeze()
            if drawn_card == "draw_3":
                chosen_player_id: str = self.decide_draw_3(game)
                game.apply_draw_3(chosen_player_id)
        else:
            raise ValueError("Drawn card not valid:", drawn_card)

        self.done = self.check_bust()

    def check_bust(self):
        # Check if list is same length after removing duplicates
        if len(self.hand.normal) != len(set(self.hand.normal)):
            if self.second_chance:
                print("Player", self.name, "used second chance to avoid bust.")
                self.hand.normal = list(set(self.hand.normal)) # Remove duplicate
                self.second_chance = False
            else:
                self.busted = True
                print("Player", self.name, "busted!")
                self.done = True

    def decide_draw(self):
        return True # TODO

    def decide_freeze(self):
        pass

    def decide_draw_3(self, game) -> str:
        """ Decide which opponent to give the draw 3 card to.
        Returns the player id to give draw_3 to.

        TODO: Make this decision smarter than random."""
        chosen_player = game.rng.choice(list(game.players))
        print("Player", self.name, "gave draw 3 to player", chosen_player.name)
        return chosen_player.id

    def count_score(self):
        if self.busted:
            return 0 

        total = 0
        for card in self.hand.normal:
            total += int(card)

        if "x2" in self.hand.bonus: # Punctuation before addition of bonuses
            total *= 2
            self.hand.bonus.remove("x2")
        for card in self.hand.bonus:
            total += int(card.replace("+", ""))
        return total



if __name__ == "__main__":
    players_state = [
        Player(hand={
            "normal": [],
            "bonus": []
        },
        name = "Marius"
        ),

        Player(hand={
            "normal": [],
            "bonus": []
        },
        name = "Thea"
        )
    ]
    game = Game(
        players = deque(players_state),
        deck_remaining = card_decks["full_deck"]
    )

    rounds_played = 0
    while not game.finished:
        game.next()
        print("len deck remaining:", len(game.deck_remaining))
        print()

        rounds_played += 1
        if rounds_played > 5:
            game.finished = True
    game.game_summary()


