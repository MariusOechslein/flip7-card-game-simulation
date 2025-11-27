import flip7
from collections import deque
import pytest


def test_normal_card_deck():
    single_player = [
        flip7.AutomaticPlayer()
    ]
    game_round = flip7.GameRound(players=deque(single_player), deck_remaining=flip7.card_decks["normal_cards_only"])
    expected_list = [
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
    assert sorted(game_round.deck_remaining) == sorted(expected_list)

def test_draw_card():
    players = [flip7.AutomaticPlayer()]
    game_round = flip7.GameRound(players=deque(players), deck_remaining=flip7.card_decks["normal_cards_only"])
    num_cards_before = len(game_round.deck_remaining)
    card = game_round.draw_card()
    assert len(game_round.deck_remaining) == num_cards_before - 1

def test_next_player_queue_setup():
    players = [flip7.AutomaticPlayer(name="Marius"), flip7.AutomaticPlayer(name="Thea")]
    game_round = flip7.GameRound(players=deque(players), deck_remaining=flip7.card_decks["normal_cards_only"])
    first_player = game_round.get_next_player()
    second_player = game_round.get_next_player()
    third_player = game_round.get_next_player()
    assert first_player.name == "Marius" and second_player.name == "Thea" and third_player.name == "Marius"

def test_valid_game_state_setups():
    players_state = [
        flip7.AutomaticPlayer(hand={
            "normal": [],
            "bonus": []
        },
        name = "Marius"
        ),

        flip7.AutomaticPlayer(hand={
            "normal": [],
            "bonus": []
        },
        name = "Thea"
        )
    ]
    # Should not raise any exceptions
    game_round = flip7.GameRound(players=deque(players_state), deck_remaining=flip7.card_decks["normal_cards_only"])

def test_invalid_player_card():
    with pytest.raises(ValueError, match="Normal Cards not valid"):
        player = flip7.AutomaticPlayer(hand={"normal": ["InvalidCard"], "bonus": []})

def test_random_seed():
    players_state = [flip7.AutomaticPlayer(name="Marius"), flip7.AutomaticPlayer(name="Thea")]
    game_round1 = flip7.GameRound(players=deque(players_state), deck_remaining=flip7.card_decks["full_deck"], seed=42)
    game_round2 = flip7.GameRound(players=deque(players_state), deck_remaining=flip7.card_decks["full_deck"], seed=42)

    draws_game1 = [game_round1.draw_card() for _ in range(5)]
    draws_game2 = [game_round2.draw_card() for _ in range(5)]
    assert draws_game1 == draws_game2

def test_apply_draw3():
    pass

def test_apply_freeze():
    pass

def test_number_of_player():
    pass

def test_player_strategies():
    pass
