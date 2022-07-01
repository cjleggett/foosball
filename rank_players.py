import numpy as np
from numpy import linalg
import requests
import csv

START_ELO = 1000


def pull_table():
    key = "1ijei0ZhIdPiY_TazfB2JZAAoNi3CWowgPquQuLv3oSU"
    sheet_name = "games"
    csv_url = f"https://docs.google.com/spreadsheets/d/{key}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    result = requests.get(url=csv_url)
    open("games.csv", "wb").write(result.content)


def read_info():
    def extract_players(game):
        columns = game.keys()
        players = {game[cname] for cname in columns if game[cname] and cname.find("player") >= 0}
        return players

    # Unpack games and players
    players_set = set()
    games = []

    with open('games.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            games.append(row)

    for game in games:
        players_set = players_set.union(extract_players(game))

    players = list(players_set)
    n_players = len(players)
    player_numbers = {players[i]: i for i in range(n_players)}

    return games, players, n_players, player_numbers


def get_game_teams(game):
    return [[player for id, player in game.items() if len(player.strip()) > 0
                and id.startswith(f"team_{i}_player") ] for i in range(1, 2 + 1)]


def rank_least_squares(games, players, n_players, player_numbers):
    # Make array of games
    games_matrix = np.zeros((len(games), n_players))
    results_array = np.zeros(len(games))
    for row, game in enumerate(games):
        # collect players
        # filter out blank names
        teams = get_game_teams(game)

        if len(teams[0]) != len(teams[1]):
            print(f"Can't score game {row} due to imbalanced teams!")
            continue

        for i, team in enumerate(teams):
            for player in team:
                games_matrix[row, player_numbers[player]] = 1 - 2 * i 
                # ^ 1 if on team 0 (1), -1 if on team 1 (2)
        results_array[row] = int(game["team_1_score"]) - int(game["team_2_score"])

    # Find Scores
    scores = linalg.lstsq(games_matrix,results_array, rcond=1)[0]
    player_scores = {players[i]: scores[i] for i in range(n_players)}
    players.sort(key=lambda p: player_scores[p], reverse=True)
    return player_scores


def calc_expected_score(team_1, team_2, elo_scores):
    team_1_rating = np.mean([elo_scores[p] for p in team_1])
    team_2_rating = np.mean([elo_scores[p] for p in team_2])
    e_team_1 = 1 / (1 + 10 ** ((team_2_rating - team_1_rating) / 500))
    return e_team_1


def calc_true_score(score_1, score_2):
    return score_1 / (score_1 + score_2)


def calc_adjusted_rating(true_score, expected_score, old_rating, max_score):
    return old_rating + .25 + 10 * max_score * (true_score - expected_score)


def rate_game(game, teams, old_elo_scores, game_id):
    if len(teams[0]) != len(teams[1]):
        print(f"Can't score game {game_id} due to imbalanced teams!")
        return

    expected_score_1 = calc_expected_score(
        teams[0],
        teams[1],
        old_elo_scores
    )

    true_score = calc_true_score(
        int(game["team_1_score"]),
        int(game["team_2_score"])
    )
    new_elo_scores = dict({})
    for team_id in range(1, 2 + 1):
        for player_id in range(1, len(teams[0]) + 1):
            new_elo_scores[game[f"team_{team_id}_player_{player_id}"]] = calc_adjusted_rating(
                (team_id - 1) + (3 - team_id * 2) * true_score,
                (team_id - 1) + (3 - team_id * 2) * expected_score_1,
                # ^ 0 + score if team 1
                #   1 - score if team 2
                old_elo_scores[teams[team_id - 1][player_id - 1]],
                max(int(game["team_1_score"]), int(game["team_2_score"]))
            )

    return new_elo_scores


def rank_elo(players, games):
    elo_scores = {player: START_ELO for player in players}
    elo_history = dict({})
    for row, game in enumerate(games):
        teams = get_game_teams(game)
        adjusted_elo_scores = rate_game(game, teams, elo_scores, row)
        elo_scores.update(adjusted_elo_scores)
        elo_history[row] = elo_scores.copy()

    return elo_scores, elo_history


def print_rankings(ls_scores, elo_scores, players):
    print("Least-Squares Ranking:")
    players.sort(key=lambda p: ls_scores[p], reverse=True)
    for i, player in enumerate(players):
        print(f"{i + 1}: {player} ({ls_scores[player]:.3f})")

    print("\n ELO Ratings:")
    players.sort(key=lambda p: elo_scores[p], reverse=True)
    for i, player in enumerate(players):
        print(f"{i + 1}: {player} ({elo_scores[player]:.3f})")
