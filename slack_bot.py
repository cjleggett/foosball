import requests
from util import ROOT_DIR, ELO_GRAPH_DIR
import subprocess
import datetime

from rank_players import pull_table, read_info, rank_elo, rank_least_squares
from plotter import anim_elo_history

IMG_LINK = "https://github.com/{your_fork}/blob/slack-bot-graphs/elo_graphs/elo.gif".format(
    your_fork = "IvanDimitrovQC/foosball"
)


def get_url():
    with open(ROOT_DIR / 'webhook_url.txt', 'r') as wh:
        url = wh.read().strip()
    return url


if __name__ == '__main__':
    current_datetime = datetime.datetime.now()

    pull_table()

    games, players, n_players, player_numbers = read_info()
    ls_scores = rank_least_squares(games, players, n_players, player_numbers)
    elo_scores, elo_history = rank_elo(players, games)

    anim_elo_history(players, games, elo_history)

    output = subprocess.check_output('sh push_to_git.sh %s %s' % (ELO_GRAPH_DIR /"elo.gif", current_datetime), shell=True)
    print("Pushed elo history.")

    webhook_url = get_url()
    r = requests.post(webhook_url, json={"img_link": IMG_LINK})
