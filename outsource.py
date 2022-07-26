# ---------------------------------------------------------------- #

import random
import logging
import datetime

# ---------------------------------------------------------------- #

def argmax(dictionary):

    max_key   = None
    max_value = -float("inf")

    for key, value in dictionary.items():
        if value > max_value:
            max_key = key
            max_value = value

    return max_key

def get_lists_top_elements(lists):
    return {
        direction_: [lists[direction_][i_][-1] for i_ in [0, 1]]
        for direction_ in ["up", "down"]
    }

def check_upgrade(lists_top_elements, card_value, direction, i):

    assert direction in {"up", "down"}

    if direction == "up":
        return lists_top_elements[direction][i] - card_value == 10
    if direction == "down":
        return card_value - lists_top_elements[direction][i] == 10

def check_play(lists_top_elements, card_value, direction, i):

    assert direction in {"up", "down"}

    if direction == "up":
        return card_value > lists_top_elements[direction][i] \
            or check_upgrade(lists_top_elements, card_value, direction, i)
    if direction == "down":
        return card_value < lists_top_elements[direction][i] \
            or check_upgrade(lists_top_elements, card_value, direction, i)

def get_play_value(lists_top_elements):
    return sum([1   - lists_top_elements["up"][i]   for i in [0, 1]]) - \
           sum([100 - lists_top_elements["down"][i] for i in [0, 1]])

# ---------------------------------------------------------------- #

class TheGame:

    LIST_ON_HAND_LENGTH = 6

    def __init__(self, players_amount, log=False):

        self.players_amount = players_amount
        self.player_turn = 0
        self.lists = {"up": [[1], [1]], "down": [[100], [100]]}

        # generate randomly permuted backup card stack
        self.list_backup = list(range(2, 100))
        random.shuffle(self.list_backup)

        # give players initial cards
        self.lists_on_hand_players = [
            [self.list_backup.pop() for _ in range(TheGame.LIST_ON_HAND_LENGTH)]
            for player_id in range(self.players_amount)
        ]

        self.log = log
        if self.log:
            date_and_time = datetime.datetime.now().strftime("%d.%m.%Y %H.%M.%S")
            logging.basicConfig(
                filename=f"{date_and_time} - {4} Players.log",
                level=logging.INFO,
                format=""
            )

    def get_plays(self, dict_reservation=None, card_multiplicity=None):

        if dict_reservation is None:
            dict_reservation = {"up": [False] * 2, "down": [False] * 2}
        if card_multiplicity is None:
            card_multiplicity = "double" if len(self.list_backup) > 0 else "single"

        plays = {}

        if card_multiplicity == "double":

            for card_1_key, card_1_value in enumerate(self.lists_on_hand_players[self.player_turn]):
                for card_2_key, card_2_value in enumerate(self.lists_on_hand_players[self.player_turn]):
                    if card_1_key != card_2_key:

                        lists_top_elements = get_lists_top_elements(self.lists)
                        for direction_1 in ["up", "down"]:
                            for i in [0, 1]:
                                if not dict_reservation[direction_1][i] or check_upgrade(lists_top_elements, card_1_value, direction_1, i):
                                    for direction_2 in ["up", "down"]:
                                        for j in [0, 1]:
                                            if not dict_reservation[direction_2][j] or check_upgrade(lists_top_elements, card_2_value, direction_2, j):

                                                lists_top_elements = get_lists_top_elements(self.lists)

                                                if check_play(lists_top_elements, card_1_value, direction_1, i):
                                                    lists_top_elements[direction_1][i] = card_1_value

                                                    if check_play(lists_top_elements, card_2_value, direction_2, j):
                                                        lists_top_elements[direction_2][j] = card_2_value

                                                        play_key = (
                                                            (card_1_key, card_1_value, direction_1, i),
                                                            (card_2_key, card_2_value, direction_2, j)
                                                        )
                                                        play_value = get_play_value(lists_top_elements)
                                                        plays[play_key] = play_value

        if card_multiplicity == "single":

            for card_key, card_value in enumerate(self.lists_on_hand_players[self.player_turn]):

                lists_top_elements = get_lists_top_elements(self.lists)
                for direction in ["up", "down"]:
                    for i in [0, 1]:
                        if not dict_reservation[direction][i] or check_upgrade(lists_top_elements, card_value, direction, i):

                            lists_top_elements = get_lists_top_elements(self.lists)

                            if check_play(lists_top_elements, card_value, direction, i):
                                lists_top_elements[direction][i] = card_value

                                play_key = (card_key, card_value, direction, i)
                                play_value = sum([1   - lists_top_elements["up"][i]   for i in [0, 1]]) - \
                                             sum([100 - lists_top_elements["down"][i] for i in [0, 1]])
                                plays[play_key] = play_value

        return plays

    def get_dict_reservation(self):

        dict_reservation = {"up": [False] * 2, "down": [False] * 2}
        reservation = False

        for player_turn_not in range(self.players_amount):
            if player_turn_not != self.player_turn:

                for card_value in self.lists_on_hand_players[player_turn_not]:

                        for i in [0, 1]:
                            if self.lists["up"][i][-1] - card_value in {10, -1, -2}:
                                dict_reservation["up"][i] = True
                                if self.log: logging.info(f"Player {player_turn_not} reserved ('up', {i}) for {card_value}")
                                reservation = True
                            if card_value - self.lists["down"][i][-1] in {10, -1}:
                                dict_reservation["down"][i] = True
                                if self.log: logging.info(f"Player {player_turn_not} reserved ('down', {i}) for {card_value}")
                                reservation = True

        if self.log and reservation: logging.info("")

        return dict_reservation

    def play_turn(self):

        # let other players reserve list(s)
        dict_reservation = self.get_dict_reservation()

        # determine values of plays
        plays_tolerant = self.get_plays(dict_reservation) # plays with    respecting reservations
        plays_ignorant = self.get_plays()                 # plays without respecting reservations

        if len(plays_ignorant) == 0:
            # even without respecting reservation the situation is hopeless
            self.game_on = False
            return

        # find keys of "best plays" without respecting reservations
        play_key_max_ignorant = argmax(plays_ignorant)

        if len(plays_tolerant) == 0:
            # with respecting reservation the situation is hopeless
            if self.log: logging.info("Ignoring reservations (no other way) ..." + "\n")
            play_key_max = play_key_max_ignorant
        else:
            play_key_max_tolerant = argmax(plays_tolerant)
            if plays_ignorant[play_key_max_ignorant] - plays_tolerant[play_key_max_tolerant] > 10:
                # with respecting reservation the situation is probably suboptimal
                if self.log: logging.info("Ignoring reservations (probably for the best) ..." + "\n")
                play_key_max = play_key_max_ignorant
            else:
                # with respecting reservation the situation is hopefully ok
                play_key_max = play_key_max_tolerant

        # play "best play"
        assert len(play_key_max) in {2, 4}
        if len(play_key_max) == 2:
            ((card_1_key, card_1_value, direction_1, i), (card_2_key, card_2_value, direction_2, j)) = play_key_max
            if self.log: logging.info(f"Playing cards {card_1_value} to {(direction_1, i)} and {card_2_value} to {(direction_2, j)} ..." + "\n")
            self.lists[direction_1][i].append(
                self.lists_on_hand_players[self.player_turn].pop(card_1_key)
            )
            if card_1_key < card_2_key: card_2_key -= 1
            self.lists[direction_2][j].append(
                self.lists_on_hand_players[self.player_turn].pop(card_2_key)
            )
        if len(play_key_max) == 4:
            (card_key, card_value, direction, i) = play_key_max
            if self.log: logging.info(f"Playing card {card_value} to {(direction, i)} ..." + "\n")
            self.lists[direction][i].append(
                self.lists_on_hand_players[self.player_turn].pop(card_key)
            )

        # lay down more cards if "appropriate"
        while True:

            # let other players reserve list(s)
            dict_reservation = self.get_dict_reservation()

            plays = self.get_plays(dict_reservation, "single")
            if len(plays) == 0: break
            play_key_max = argmax(plays)
            play_value_new = plays[play_key_max]

            play_value_old = get_play_value(get_lists_top_elements(self.lists))

            if play_value_old - play_value_new <= 2: # appropriate?
                (card_key, card_value, direction, i) = play_key_max
                if self.log: logging.info(f"Playing card {card_value} to {(direction, i)} ..." + "\n")
                self.lists[direction][i].append(
                    self.lists_on_hand_players[self.player_turn].pop(card_key)
                )
            else:
                break

        # take enough cards from stack
        while len(self.list_backup) > 0 \
          and len(self.lists_on_hand_players[self.player_turn]) < TheGame.LIST_ON_HAND_LENGTH:
            self.lists_on_hand_players[self.player_turn].append(
                self.list_backup.pop()
            )

    def play_round(self):

        if self.log:
            logging.info("Backup card stack:")
            logging.info(str(self.list_backup))
            logging.info("")

        for _ in range(self.players_amount):
            if self.game_on and len(self.lists_on_hand_players[self.player_turn]) > 0:

                if self.log:
                    logging.info("#" + " " + "-"*32 + " " + "#" + "\n")
                    logging.info(f"Player's turn: {self.player_turn}")
                    logging.info("")

                if self.log:
                    logging.info("Lists to lay down cards (before):")
                    for key, value in self.lists.items():
                        logging.info(f"{key}: {value[0]}" + "\n" + " "*(len(key) + 2) + str(value[1]))
                    logging.info("")

                if self.log:
                    logging.info("Player's lists on hand:")
                    for player_id in range(self.players_amount):
                        logging.info(f"Player {player_id}: {self.lists_on_hand_players[player_id]}")
                    logging.info("")

                self.play_turn()

                if self.log:
                    logging.info("Lists to lay down cards (after):")
                    for key, value in self.lists.items():
                        logging.info(f"{key}: {value[0]}" + "\n" + " "*(len(key) + 2) + str(value[1]))
                    logging.info("")

            # make next round be next players turn
            self.player_turn += 1

        self.player_turn = 0

    def play_game(self, max_round=float("inf")):

        if self.log:
            with open("title.txt") as f:
                logging.info(f.read().replace("Â", "") + "\n")
            logging.info("#" + " " + "-"*64 + " " + "#" + "\n")

        self.game_on = True

        round_counter = 0
        while self.game_on and round_counter < max_round:

            # check for win
            if sum([len(list_on_hand_player) for list_on_hand_player in self.lists_on_hand_players]) == 0:
                self.game_on = False
                break

            round_counter += 1

            if self.log:
                logging.info(f"Round: {round_counter}")
                logging.info("")

            self.play_round()

            if self.log: logging.info("#" + " " + "-"*64 + " " + "#" + "\n")
        
        logging.info("End of TheGame!")
        laid_down_cards = len(self.lists["up"][0])-1 + len(self.lists["down"][0])-1 \
                        + len(self.lists["up"][1])-1 + len(self.lists["down"][1])-1
        logging.info(f"Laid down cards: {laid_down_cards} / {98} ~ {round(laid_down_cards / 98 * 100, 2)}%")

# ---------------------------------------------------------------- #
