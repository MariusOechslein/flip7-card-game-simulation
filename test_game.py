import flip7
from collections import deque
import pytest


def test_normal_card_deck():
    single_player = [
        flip7.Player()
    ]
    game = flip7.Game(players=deque(single_player), deck_remaining=flip7.card_decks["normal_cards_only"])
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
    assert game.deck_remaining == expected_list

def test_draw_card():
    players = [flip7.Player()]
    game = flip7.Game(players=deque(players), deck_remaining=flip7.card_decks["normal_cards_only"])
    num_cards_before = len(game.deck_remaining)
    card = game.draw_card()
    assert len(game.deck_remaining) == num_cards_before - 1

def test_next_player_queue_setup():
    players = [flip7.Player(name="Marius"), flip7.Player(name="Thea")]
    game = flip7.Game(players=deque(players), deck_remaining=flip7.card_decks["normal_cards_only"])
    first_player = game.next_player()
    second_player = game.next_player()
    third_player = game.next_player()
    assert first_player.name == "Marius" and second_player.name == "Thea" and third_player.name == "Marius"

def test_valid_game_state_setups():
    players_state = [
        flip7.Player(hand={
            "normal": [],
            "bonus": []
        },
        name = "Marius"
        ),

        flip7.Player(hand={
            "normal": [],
            "bonus": []
        },
        name = "Thea"
        )
    ]
    # Should not raise any exceptions
    game = flip7.Game(players=deque(players_state), deck_remaining=flip7.card_decks["normal_cards_only"])

def test_invalid_player_card():
    with pytest.raises(ValueError, match="Normal Cards not valid"):
        player = flip7.Player(hand={"normal": ["InvalidCard"], "bonus": []})

def test_draw_3_card():
    players_state = [flip7.Player(name="Marius"), flip7.Player(name="Thea")]
    game = flip7.Game(players=deque(players_state), deck_remaining=flip7.card_decks["full_deck"], seed=42)
    game.apply_draw_3(to_player_id=game.players[0].id)
    assert game.players[0].hand.normal == ["5", "2"] and game.players[0].hand.bonus == ["+4"]

def test_random_seed():
    players_state = [flip7.Player(name="Marius"), flip7.Player(name="Thea")]
    game1 = flip7.Game(players=deque(players_state), deck_remaining=flip7.card_decks["full_deck"], seed=42)
    game2 = flip7.Game(players=deque(players_state), deck_remaining=flip7.card_decks["full_deck"], seed=42)

    draws_game1 = [game1.draw_card() for _ in range(5)]
    draws_game2 = [game2.draw_card() for _ in range(5)]
    assert draws_game1 == draws_game2
