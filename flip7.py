import random
import logging
from collections import deque # For next player rotations
from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing import List
from uuid import uuid4
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='game.log',
    filemode='w'
)
logger = logging.getLogger(__name__)

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

NORMAL_CARDS = {str(i) for i in range(13)}  # "0"..."12"
BONUS_CARDS = {"x2", "+2", "+4", "+6", "+8", "+10"}
SPECIAL_CARDS = {"freeze", "second_chance", "draw_3"}

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
        self.rng.shuffle(self.deck_remaining)

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
        from_card_list = NORMAL_CARDS | BONUS_CARDS | SPECIAL_CARDS
        for c in v:
            if c not in from_card_list:
                raise ValueError(f"Invalid card in deck: {c}")
        return v

    def next(self):
        if self.finished:
            return

        player = self.get_next_player()

        self._execute_player_turn(player)

        self.finished = self.check_game_finished()

    def _execute_player_turn(self, player):
        if player.done or player.busted:
            return
        logger.info(f"Player: {player.name} turn.")

        drawn_card = self.draw_card()
        logger.info(f"Card drawn: {drawn_card}")

        player.receive_card(drawn_card)
        busted: bool = player.check_bust()
        if busted:
            if player.second_chance:
                player.second_chance = False
                player.hand.normal.pop() # Assumes last cards are appended at the end.
                logger.info(f"Player {player.name} busted but used second chance.")
            else:
                player.busted = True
                player.done = True
                logger.info(f"Player {player.name} busted.")

        if drawn_card in SPECIAL_CARDS:
            if drawn_card == "freeze":
                player_id_to_freeze: str = player.decide_freeze()
                self.apply_freeze(player_id_to_freeze)
            if drawn_card == "draw_3":
                player_id_to_draw3: str = player.decide_draw_3(self)
                self.apply_draw_3(player_id_to_draw3)
            if drawn_card == "second_chance":
                player.second_chance = True # Always applied to player who draws it
                logger.info(f"Player {player.name} received second chance special card.")


    def get_next_player(self):
        next_player = self.players[0]
        self.players.rotate(-1)
        return next_player

    def draw_card(self):
        card = self.deck_remaining.pop()
        return card

    def apply_draw_3(self, to_player_id: str):
        pass

    def apply_freeze(self, to_player_id: str):
        pass # TODO

    def check_game_finished(self):
        all_done = all(player.done or player.busted for player in self.players)
        if all_done:
            return True
        if len(self.deck_remaining) == 0:
            logger.info("Deck is empty, finishing game.")
            return True
        return False


    def game_summary(self):
        logger.info(f"Player scores:")
        for i, player in enumerate(self.players):
            logger.info(f"Player {str(i)} score: {count_score(player)} hand: {player.hand.normal} bonus: {player.hand.bonus} special_cards_log: {player.hand.special_cards_log} busted: {player.busted}")



class Hand(BaseModel):
    normal: List[str] = Field(default=[], description="List of normal cards in hand.")
    bonus: List[str] = Field(default=[], description="List of bonus cards in hand.")
    special_cards_log: List[str] = Field(default=[], description="List of special cards in hand.")

    @field_validator("normal", mode="before")
    def check_normal(cls, v):
        for card in v:
            if not card in NORMAL_CARDS:
                raise ValueError("Normal Cards not valid")
        return v

    @field_validator("bonus", mode="before")
    def check_bonus(cls, v):
        for card in v:
            if not card in BONUS_CARDS:
                raise ValueError("Bonus Cards not valid")
        return v

    @field_validator("special_cards_log", mode="before")
    def check_special_cards_log(cls, v):
        for card in v:
            if not card in SPECIAL_CARDS:
                raise ValueError("Special Cards not valid")
        return v


class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the player.")
    done: bool = Field(default=False, description="Boolean indicating if the player is done playing this round.")
    busted: bool = Field(default=False, description="Boolean indicating if the player has busted this round.")
    in_draw_3: bool = Field(default=False, description="Boolean indicating if the player is currently affected by a 'draw 3' card.")
    hand: Hand = Field(default_factory=Hand, description="Player's hand containing normal and bonus cards.")
    second_chance: bool = Field(default=False, description="Boolean indicating if the player has a second chance special card to use against busting.")
    name: str = Field(default="Unknown Player", description="Name of the player.")

    def receive_card(self, card: str):
        if card in NORMAL_CARDS:
            self.hand.normal.append(card)
        elif card in BONUS_CARDS:
            self.hand.bonus.append(card)
        elif card in SPECIAL_CARDS:
            self.hand.special_cards_log.append(card)
        else:
            raise ValueError("Drawn card not valid:", card)

    def decide_draw(self):
        return True # TODO

    def decide_freeze(self) -> str:
        """ Decide which opponent to freeze.
        Returns the player id to freeze."""
        # TODO: Make this smarter than random
        chosen_player = game.rng.choice(list(game.players))
        logger.info(f"Player {self.name} gave to freeze player {chosen_player.name}")
        return chosen_player.id

    def decide_draw_3(self, game) -> str:
        """ Decide which opponent to give the draw 3 card to.
        Returns the player id to give draw_3 to.

        TODO: Make this decision smarter than random."""
        chosen_player = game.rng.choice(list(game.players))
        logger.info(f"Player {self.name} gave draw 3 to player {chosen_player.name}")
        return chosen_player.id

    def check_bust(self: Player) -> bool:
        if len(self.hand.normal) != len(set(self.hand.normal)): # Check if list is same length after removing duplicates
            return True
        return False


# Util function
def count_score(player: Player) -> int:
    if player.busted:
        return 0

    total = sum(int(c) for c in player.hand.normal)

    multiply = 2 if "x2" in player.hand.bonus else 1
    total *= multiply

    total += sum(int(b.replace("+", "")) for b in player.hand.bonus if b != "x2")

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

    count = 0
    while not game.finished:
        game.next()
        logger.info(f"len deck remaining: {len(game.deck_remaining)}.")

        count += 1
        if count > 7:
            logger.info("Max turns reached, ending game to avoid infinite loop.")
            break

    game.game_summary()


