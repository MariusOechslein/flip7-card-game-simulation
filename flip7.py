"""TODO: Use Pydantic! TODO: Use Logging library! TODO: Use Debugger for errors!"""

import random
from collections import deque # For next player rotations
import copy
from pydantic import BaseModel, field_validator, model_validator, Field
from typing import List

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
    ]
}

class Game(BaseModel):
    finished: bool = Field(default=False, description="Boolean indicating if the game is finished.")
    players: deque = Field(..., description="Deque of Player objects representing the players in the game and turn order.")
    deck_remaining: List[str] = Field(..., description="List of strings representing the remaining cards in the deck.")

    @field_validator("players", mode="before")
    @classmethod
    def check_players(cls, v):
        if not isinstance(v, deque):
            raise ValueError("players must be a deque")
        if len(v) < 1:
            raise ValueError("must have at least 1 player")
        return v

    @model_validator(mode="after")
    def validate_game_state(self):
        """Validating game state of players hands and deck remaining."""
        all_player_cards = [player.hand.normal for player in self.players]
        flat_all_player_cards = [int(item) for sublist in all_player_cards for item in sublist] # Flat out nested lists # TODO: Risky to do int() here. Should be solved with strong typing by pydantic models.
        deck_state_values = [int(card) for card in self.deck_remaining]

        all_value_cards_in_play = deck_state_values + flat_all_player_cards
        if any(n < 0 or n > 12 for n in all_value_cards_in_play):
            raise ValueError("Error in validate_game_state(): Value below 0 or above 12 in game_state.")
        len_all_value_cards_in_play = len(all_value_cards_in_play)
        if len_all_value_cards_in_play != 79:
            raise ValueError("Error in validate_game_state(): Not 79 value cards in play.")
        if sum(all_value_cards_in_play) != 650:
            raise ValueError("Error in validate_game_state(): Sum of value cards")
        return self

    def next(self):
        if self.finished:
            print("Game is over.")
            for i, player in enumerate(self.players):
                print("Player", str(i), "score:", player.count_score())
            return

        next_player = self.next_player()
        next_player.play()

    def next_player(self):
        next_player = self.players[0]
        next_player.turns_remaining -= 1
        if next_player.turns_remaining == 0: # Only False if player got special "draw 3" card.
            self.players.rotate(-1)
            next_player.turns_remaining = 1 # Reset
        return next_player

    def draw_card(self):
        card = random.choice(self.deck_remaining)
        self.deck_remaining.remove(card)
        return card

    def game_summary(self):
        print("Player scores:")
        for i, player in enumerate(self.players):
            print("Player", str(i), "score:", player.count_score(), "hand:", player.hand.normal, "bonus:", player.hand.bonus, "busted:", player.busted)



class Hand(BaseModel):
    normal: List[str] = Field(default=[], description="List of normal cards in hand.")
    bonus: List[str] = Field(default=[], description="List of bonus cards in hand.")

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
                raise ValueError("Cards must be numeric strings")
        return v


class Player(BaseModel):
    done: bool = Field(default=False, description="Boolean indicating if the player is done playing this round.")
    busted: bool = Field(default=False, description="Boolean indicating if the player has busted this round.")
    turns_remaining: int = Field(default=1, description="Number of turns remaining for the player in the current round. Important for special 'draw 3' card.")
    hand: Hand = Field(default=Hand(), description="Player's hand containing normal and bonus cards.")
    second_chance: bool = Field(default=False, description="Boolean indicating if the player has a second chance special card to use against busting.")
    name: str = Field(default="Unknown Player", description="Name of the player.")

    def play(self):
        print("Player:", self.name, "turn.")
        if self.done:
            return

        if self.decide_draw() == False:
            self.done = True
            return

        drawn_card = game.draw_card()
        if drawn_card in ["0","1","2","3","4","5","6","7","8","9","10","11","12"]:
            self.hand.normal.append(drawn_card)
        else:
            # TODO: Handle non-normal cards
            pass
        print("Card drawn:", drawn_card)
        print("Hand:", self.hand.normal)

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
    global game
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
        deck_remaining = card_decks["normal_cards_only"]
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


