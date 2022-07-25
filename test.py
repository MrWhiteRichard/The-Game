from outsource import TheGame

players_amount = 4
thegame = TheGame(players_amount)
thegame.play_game(debug=True)

print("End of TheGame!")
laid_down_cards = len(thegame.lists["up"][0])-1 + len(thegame.lists["down"][0])-1 \
                + len(thegame.lists["up"][1])-1 + len(thegame.lists["down"][1])-1
print(f"Laid down cards: {laid_down_cards} / {98} ≈ {round(laid_down_cards / 98 * 100, 2)}%")