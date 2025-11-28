import random
import logging
from collections import deque # For next player rotations
from pydantic import BaseModel, field_validator, Field, ConfigDict
from typing import List
from uuid import uuid4
from enum import Enum
from abc import ABC, abstractmethod

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

class TargetingStrategy(str, Enum):
    RANDOM = "random"
    RANDOM_OPPONENT = "random_opponent"
    LOWEST_SCORE = "lowest_score"
    HIGHEST_SCORE = "highest_score"

class DrawingStrategy(str, Enum):
    ALWAYS = "always"
    NEVER = "never"
    BELOW_25_VALUE = "below_25_value"
    BELOW_3_CARDS = "below_3_cards"


class Game(BaseModel):
    """Plays multiple GameRounds until one player reaches 200 points."""
    winning_score: int = Field(default=200, description="Score needed to win the game.")
    finished: bool = Field(default=False, description="Boolean indicating if the game is finished.")
    players: List[PlayerBase] = Field(..., description="List of Player objects participating in the game.")

    def play(self):
        while not self.finished:
            game_round = GameRound(
                players = deque(self.get_players_for_new_round()),
                deck_remaining = card_decks["full_deck"]
            )
            while not game_round.finished:
                game_round.next()
            game_round.game_summary()
            self.update_player_scores(game_round)
            self.finished = self.check_game_finished()

    def update_player_scores(self, game_round: GameRound):
        for player in game_round.players:
            round_score = count_score(player)
            player.total_score += round_score
            logger.info(f"Player {player.name} scored {round_score} this round. Total score: {player.total_score}.")

    def check_game_finished(self):
        for player in self.players:
            if player.total_score >= self.winning_score:
                logger.info(f"Player {player.name} has won the game with a total score of {player.total_score}!")
                return True
        return False

    def get_players_for_new_round(self) -> List[PlayerBase]:
        # Rotate starting players
        self.players.append(self.players.pop(0))

        # Reset player states for new round
        for player in self.players:
            player.done = False
            player.busted = False
            player.second_chance = False
            player.hand = Hand()
        return self.players


class GameRound(BaseModel):
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

        self.finished = self.check_game_round_finished()


    def _execute_player_turn(self, player):
        if player.done or player.busted:
            return
        logger.info(f"Player: {player.name} turn.")

        wants_to_draw: bool = player.decide_draw(self)
        if not wants_to_draw:
            player.done = True
            logger.info(f"Player {player.name} decided to stop drawing cards.")
            return

        self._execute_player_draw(player)

    def _execute_player_draw(self, player):
        drawn_card = self.draw_card()
        logger.info(f"Card drawn: {drawn_card}")

        player.receive_card(drawn_card)
        busted: bool = player.check_bust()
        if busted: # Refactor to function
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
                targeting_strategy: TargetingStrategy = player.decide_freeze_strategy(self)
                target: PlayerBase = self.choose_player_by_targeting_strategy(player, targeting_strategy)
                logger.info(f"Player {player.name} chose to freeze Player {target.name}.")
                self.apply_freeze_effect(target)

            if drawn_card == "draw_3":
                targeting_strategy: TargetingStrategy = player.decide_draw_3_strategy(self)
                target: PlayerBase = self.choose_player_by_targeting_strategy(player, targeting_strategy)
                logger.info(f"Player {player.name} chose to give draw 3 to Player {target.name}.")
                self.apply_draw_3_effect(target)

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

    def apply_freeze_effect(self, target: PlayerBase):
        target.done = True
        logger.info(f"Player {target.name} has been frozen and cannot draw more cards this round.")

    def apply_draw_3_effect(self, player: PlayerBase):
        for i in range(3):
            self._execute_player_draw(player)
    
    def choose_player_by_targeting_strategy(self, chooser: PlayerBase, targeting_strategy: TargetingStrategy) -> PlayerBase:
        valid_players = [p for p in self.players if not p.done and not p.busted]
        if not valid_players:
            return None

        if targeting_strategy == TargetingStrategy.RANDOM:
            return self.rng.choice(valid_players)
        elif targeting_strategy == TargetingStrategy.RANDOM_OPPONENT:
            valid_opponents = [p for p in valid_players if p.id != chooser.id]
            return self.rng.choice(valid_opponents)
        elif targeting_strategy == TargetingStrategy.LOWEST_SCORE:
            return min(valid_players, key=lambda p: count_score(p))
        elif targeting_strategy == TargetingStrategy.HIGHEST_SCORE:
            return max(valid_players, key=lambda p: count_score(p))
        else:
            raise ValueError("Invalid choose player option:", targeting_strategy)

    def check_game_round_finished(self):
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
            logger.info(f"Player {str(player.name)} score: {count_score(player)} hand: {player.hand.normal} bonus: {player.hand.bonus} special_cards_log: {player.hand.special_cards_log} busted: {player.busted}")



class Hand(BaseModel):
    normal: List[str] = Field(default=list(), description="List of normal cards in hand.")
    bonus: List[str] = Field(default=list(), description="List of bonus cards in hand.")
    special_cards_log: List[str] = Field(default=list(), description="List of special cards in hand.")

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
        if not isinstance(v, list):
            raise ValueError("special_cards_log must be a list")
        for card in v:
            if not card in SPECIAL_CARDS:
                raise ValueError("Special Cards not valid")
        return v


class PlayerBase(BaseModel, ABC): # Abstract Base Class for Player
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier for the player.")
    done: bool = Field(default=False, description="Boolean indicating if the player is done playing this round.")
    busted: bool = Field(default=False, description="Boolean indicating if the player has busted this round.")
    second_chance: bool = Field(default=False, description="Boolean indicating if the player has a second chance special card to use against busting.")
    name: str = Field(default="Unknown Player", description="Name of the player.")
    total_score: int = Field(default=0, description="Total score of the player across rounds.")

    hand: Hand = Field(default_factory=Hand, description="Player's hand containing normal and bonus cards.")

    @abstractmethod
    def decide_draw(self, game: GameRound) -> bool:
        pass

    @abstractmethod
    def decide_freeze_strategy(self, game: GameRound) -> TargetingStrategy:
        pass

    @abstractmethod
    def decide_draw_3_strategy(self, game: GameRound) -> TargetingStrategy:
        pass

    def receive_card(self, card: str):
        if card in NORMAL_CARDS:
            self.hand.normal.append(card)
        elif card in BONUS_CARDS:
            self.hand.bonus.append(card)
        elif card in SPECIAL_CARDS:
            self.hand.special_cards_log.append(card)
        else:
            raise ValueError("Drawn card not valid:", card)

    def check_bust(self) -> bool:
        if len(self.hand.normal) != len(set(self.hand.normal)): # Check if list is same length after removing duplicates
            return True
        return False

class AutomaticPlayer(PlayerBase):
    targeting_strategy: TargetingStrategy = Field(default=TargetingStrategy.RANDOM, description="Player's targeting strategy for special cards.")
    drawing_strategy: DrawingStrategy = Field(default=DrawingStrategy.BELOW_25_VALUE, description="Player's drawing strategy for deciding whether to draw more cards.")

    def decide_draw(self, game: GameRound) -> bool:
        """ Decide whether to draw a card or stop.
        Returns True to draw, False to stop."""
        if self.drawing_strategy == DrawingStrategy.ALWAYS:
            return True
        elif self.drawing_strategy == DrawingStrategy.NEVER:
            return False
        elif self.drawing_strategy == DrawingStrategy.BELOW_25_VALUE:
            current_score = count_score(self)
            return current_score < 25
        elif self.drawing_strategy == DrawingStrategy.BELOW_3_CARDS:
            return len(self.hand.normal) < 3
        else:
            raise ValueError("Invalid drawing strategy:", self.drawing_strategy)

    def decide_freeze_strategy(self, game: GameRound) -> TargetingStrategy:
        """ Decide which opponent to freeze.
        Returns the player id to freeze."""
        return self.targeting_strategy

    def decide_draw_3_strategy(self, game) -> TargetingStrategy:
        """ Decide which opponent to give the draw 3 card to.
        Returns the player id to give draw_3 to."""
        return self.targeting_strategy

class InteractivePlayer(PlayerBase):
    def decide_draw(self, game: GameRound) -> bool:
        choice: str = self.choice_interface("do you want to draw a card?", ['y', 'n'])
        return choice == 'y'

    def decide_freeze_strategy(self, game: GameRound) -> TargetingStrategy:
        choice: TargetingStrategy = self.choice_interface("Choose targeting strategy for freeze", TargetingStrategy._value2member_map_.keys())
        return TargetingStrategy(choice)

    def decide_draw_3_strategy(self, game) -> TargetingStrategy:
        choice: TargetingStrategy = self.choice_interface("Choose targeting strategy for draw 3", TargetingStrategy._value2member_map_.keys())
        return TargetingStrategy(choice)

    def choice_interface(self, prompt: str, options: List[str]) -> str:
        print(f"\n{self.name}'s turn. Current hand: Normal Cards: {self.hand.normal}, Bonus Cards: {self.hand.bonus}, Special Cards: {self.hand.special_cards_log}\n")
        while True:
            choice = input(f"{self.name}, {prompt} ({', '.join(options)}): ").strip().lower()
            if choice in options:
                return choice
            else:
                print(f"Invalid input. Please enter one of the following options: {', '.join(options)}.")


# Util function
def count_score(player: PlayerBase) -> int:
    if player.busted:
        return 0

    total = sum(int(c) for c in player.hand.normal)

    multiply = 2 if "x2" in player.hand.bonus else 1
    total *= multiply

    total += sum(int(b.replace("+", "")) for b in player.hand.bonus if b != "x2")

    return total



if __name__ == "__main__":
    players_state = [
        AutomaticPlayer(name = "Marius"),
        AutomaticPlayer(name = "Thea"),
        #InteractivePlayer(name = "You"),
    ]
    game = Game(
        players = players_state,
        deck_remaining = card_decks["full_deck"]
    )

    game.play()

    logger.info("Game finished.")
