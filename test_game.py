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
    
        





test_normal_card_deck()
test_draw_card()
test_next_player_queue_setup()
test_valid_game_state_setups()
test_game_state_setups()


print()
