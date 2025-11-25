"""TODO: Use pytest!"""

import flip7
import copy
from collections import deque


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
    if game.deck_remaining == expected_list:
        print("Deck Normal_cards_only --- Passed")
    else:
        print("Deck Normal_cards_only --- Error")

def test_draw_card():
    players = [flip7.Player()]
    game = flip7.Game(players=deque(players), deck_remaining=flip7.card_decks["normal_cards_only"])
    num_cards_before = len(game.deck_remaining)
    card = game.draw_card()
    if len(game.deck_remaining) == num_cards_before - 1:
        print("Draw card --- Passed")
    else:
        print("Draw card --- Error")

def test_next_player_queue_setup():
    players = [flip7.Player(name="Marius"), flip7.Player(name="Thea")]
    game = flip7.Game(players=deque(players), deck_remaining=flip7.card_decks["normal_cards_only"])
    first_player = game.next_player()
    second_player = game.next_player()
    third_player = game.next_player()
    if first_player.name == "Marius" and second_player.name == "Thea" and third_player.name == "Marius":
        print("test_next_player_queue_setup --- Passed")
    else:
        print("test_next_player_queue_setup --- Error")

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
    try:
        game = flip7.Game(players=deque(players_state), deck_remaining=flip7.card_decks["normal_cards_only"])
        print("Valid game state setup --- Passed")
    except:
        print("Valid game state setup --- Error")

def test_game_state_setups():
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
    try:
        faulty_player_state = copy.deepcopy(players_state)
        faulty_player_state[0].hand["normal"] = ["10"]

        game = flip7.Game(players=deque(faulty_player_state), deck_remaining=flip7.card_decks["normal_cards_only"])
        print("Faulty game state setup --- Error")
    except:
        print("Faulty game state setup --- Passed")
    

def test_pydantic_models():
    players_state = [flip7.Player(), flip7.Player()]
    faulty_deck = copy.deepcopy(flip7.card_decks["normal_cards_only"])
    faulty_deck.append("ExtraCard")  # Invalid card to test pydantic validation
    try:
        game = flip7.Game(players=deque(players_state), deck_remaining=faulty_deck)
        print("Pydantic model validation --- Error: Should have failed but didn't")
    except:
        print("Pydantic model validation --- Passed")

def test_draw_3_card():
    players_state = [flip7.Player(name="Marius"), flip7.Player(name="Thea")]
    game = flip7.Game(players=deque(players_state), deck_remaining=flip7.card_decks["full_deck"], seed=42)
    game.apply_draw_3(to_player_id=game.players[0].id)
    if game.players[0].hand.normal == ["5", "2"] and game.players[0].hand.bonus == ["+4"]:
        print("Draw 3 card application --- Passed")
    else:
        print("Draw 3 card application --- Error")

def test_random_seed():
    players_state = [flip7.Player(name="Marius"), flip7.Player(name="Thea")]
    game1 = flip7.Game(players=deque(players_state), deck_remaining=flip7.card_decks["full_deck"], seed=42)
    game2 = flip7.Game(players=deque(players_state), deck_remaining=flip7.card_decks["full_deck"], seed=42)

    draws_game1 = [game1.draw_card() for _ in range(5)]
    draws_game2 = [game2.draw_card() for _ in range(5)]
    if draws_game1 == draws_game2:
        print("Random seed consistency --- Passed")
    else:
        print("Random seed consistency --- Error")



test_normal_card_deck()
test_draw_card()
test_next_player_queue_setup()
test_valid_game_state_setups()
test_game_state_setups()
test_pydantic_models()
test_draw_3_card()
test_random_seed()


print()
