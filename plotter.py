import matplotlib.pyplot as plt
from matplotlib import animation
import pandas as pd
import numpy as np
from rank_players import get_game_teams
from util import ELO_GRAPH_DIR
from scipy.interpolate import make_interp_spline

def plot_elo_history(player, games, elo_history):
    def check_if_played(game):
        game_teams = get_game_teams(game)
        return (player in game_teams[0]) | (player in game_teams[1])

    player_games = [g_id for g_id, g in enumerate(games) if check_if_played(g)]
    player_elo = [1000]
    player_elo.extend([elo_history[g_id][player] for g_id in player_games])
    # start from 1, 0th will be initial elo
    updated_games = [0]
    updated_games.extend([g_id + 1 for g_id in player_games])

    fig = plt.figure()
    fig.subplots_adjust(top=0.8)
    ax1 = fig.add_subplot(211)
    ax1.set_ylabel('elo')
    ax1.set_title('{} elo history'.format(player))
    ax1.set_xlabel('Game #ID')

    ax1.plot(updated_games, player_elo, '-o')
    fname = ELO_GRAPH_DIR / "{}_elo_history.png".format(player)
    plt.savefig(fname)

def anim_elo_history(players, games, elo_history):
    # get elo as df with columns player names
    trajs = pd.DataFrame(elo_history).T
    # append start rating of 1000 for players of the first game
    # (hence game -1 is just everyone at 1000)
    trajs.loc[-1] = 1000
    trajs = trajs.sort_index()

    # get first game played
    first_games = {}
    for player in players:
        for i, game in enumerate(games):
            game_teams = get_game_teams(game)
            if (player in game_teams[0]) | (player in game_teams[1]):
                first_games[player] = i
                break

    # fixed at 30FPS
    INTERVAL = 1 / 60 * 1000 # not actually matters
    FPS = 35
    TOTAL_RUNTIME = 5 # in seconds
    FRAMES_PER_GAME = TOTAL_RUNTIME * FPS // (len(games) + 1)
    plt.close('all')
    fig, ax = plt.subplots(1, 1, figsize = (6, 3))

    EASE_IN_FUNC = lambda t: t # ** 2
    EASE_OUT_FUNC = lambda t: 1 - t # ** 2

    # animation for frame i
    def animate(i):
        BASE_LINEWIDTH = 1.5
        MAX_ADDL_LINEWIDTH = 1.5
        BASE_MARKERSIZE = 18
        MAX_ADDL_MARKERSIZE = 36
        # clear plot
        ax.cla()

        # time starts at -1 and ends at len(games)
        curr_time_as_game = i / FRAMES_PER_GAME - 1

        # collect current and next players for fadeout/in
        curr_game = int(np.floor(curr_time_as_game))
        curr_players = []
        next_players = []
        if curr_game >= 0 and curr_game < len(games):
            curr_players = [p for t in get_game_teams(games[curr_game]) for p in t]
        next_game = int(np.floor(curr_time_as_game + 1))
        if next_game < len(games):
            next_players = [p for t in get_game_teams(games[next_game]) for p in t]
        delta = curr_time_as_game - curr_game # fraction of time passed

        for player in players:
            # blank plots for people who haven't played their first game
            if curr_time_as_game < first_games[player] - 1:
                ax.plot([], [])
                ax.scatter([], [], label = player)
                continue
        
            # support for x axis, take game before to start at 1000
            xsup = np.arange(first_games[player] - 1, len(games))
            # finer grain for spline, with one increment per frame
            xnew = np.linspace(min(xsup), max(xsup), FRAMES_PER_GAME * (len(xsup) - 1) + 1)

            # get elos for the player over their support
            trunc_traj = trajs[player][xsup]
            spl = make_interp_spline(xsup, trunc_traj, min(3, len(xsup) - 1))

            # filter to only plot up to current time
            xnew = xnew[xnew <= curr_time_as_game]
            trunc_traj = list(trunc_traj[xsup <= curr_time_as_game])
            xsup = xsup[xsup <= curr_time_as_game]
            spline_path = spl(xnew)

            # for those in both curr and next, take max adjustment
            width_adjustment_queue = []
            if player in curr_players:
                width_adjustment_queue.append(EASE_OUT_FUNC(delta))
            if player in next_players:
                width_adjustment_queue.append(EASE_IN_FUNC(delta))
            width_adjustment = 0 if not len(width_adjustment_queue) else max(width_adjustment_queue)

            marker_sizes = [BASE_MARKERSIZE + MAX_ADDL_MARKERSIZE if game >= 0 and player in games[game].values() 
                                else BASE_MARKERSIZE for game in xsup]
            ax.plot(1 + xnew, spline_path, linewidth = BASE_LINEWIDTH, alpha = 0.8) # + width_adjustment * MAX_ADDL_LINEWIDTH determined looks ugly
            # append on point in current time to have line end with a dot
            ax.scatter(list(1 + xsup) + [xnew[-1] + 1], trunc_traj + [spline_path[-1]], label = player, 
                        s = marker_sizes + [BASE_MARKERSIZE + width_adjustment * MAX_ADDL_MARKERSIZE], alpha = 0.8)
        # fix x-axis 
        # possible change: sliding x/y axis
        ax.set_xlim([0, len(games)])
        Y_MIN = trajs.min().min()
        Y_MAX = trajs.max().max()
        Y_RANGE = Y_MAX - Y_MIN
        ax.set_ylim([Y_MIN - Y_RANGE / 10, Y_MAX + Y_RANGE / 10])
        ax.legend(loc = "center left", bbox_to_anchor = (1, 0.5))
        fig.tight_layout()

    anim = animation.FuncAnimation(fig, animate, frames = range(1, FRAMES_PER_GAME * len(games) + FPS + 1), interval = INTERVAL / 10, blit = False)
    anim.save("elo_graphs/elo.gif", animation.ImageMagickWriter(fps = FPS))
