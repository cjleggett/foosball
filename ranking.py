from __future__ import annotations

import csv
import datetime
import statistics
import io
from dataclasses import dataclass, field
from typing import Iterable, Optional, Any


FREE_ELO_GAIN = 0.25
ELO_GAIN_COEF = 10
INITIAL_ELO = 1000


@dataclass
class TeamResult:
    players: tuple[str, ...]
    points: int

    def __post_init__(self):
        assert self.players, "The has to be at least one player"
        assert self.points >= 0, "The score has to be non-negative"


@dataclass
class Match:
    results: tuple[TeamResult, TeamResult]
    when: Optional[datetime.datetime] = field(default_factory=lambda: None)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        assert not (set(self.results[0].players) & set(self.results[1].players)), \
            "A player can only be on one team"

    @property
    def teams(self) -> tuple[tuple[str], tuple[str]]:
        return self.results[0].players, self.results[1].players

    @property
    def points(self) -> tuple[int, int]:
        return self.results[0].points, self.results[1].points

    @property
    def players(self) -> set[str]:
        return set(self.results[0].players) | set(self.results[1].players)


class RankingSystem:
    elo: dict[str, float]
    match_history: list[Match]
    free_elo_gain: float
    elo_gain_coef: float

    def __init__(self, matches: Iterable[Match] = (), *,
                 free_elo_gain: float = FREE_ELO_GAIN, elo_gain_coef: float = ELO_GAIN_COEF,
                 initial_elo: float = INITIAL_ELO):
        self.elo = {}
        self.match_history = []
        self.free_elo_gain = free_elo_gain
        self.elo_gain_coef = elo_gain_coef
        self.initial_elo = initial_elo

        for match in matches:
            self.score_match(match)

    @property
    def ranking(self) -> list[tuple[str, float]]:
        player_ranking = sorted(self.elo, key=lambda player: self.elo[player])
        return [(player, self.elo[player]) for player in player_ranking]

    def team_elo(self, team: tuple[str]) -> float:
        return statistics.mean(self.elo[player] for player in team)

    def player_team_weight(self, player: str, team: tuple[str]) -> float:
        return 1

    def score_sigmoid(self, x: float) -> float:
        return 1 / (1 + 10 ** (x / 500))

    def pred_score(self, first: tuple[str], second: tuple[str]) -> float:
        ratings = (self.team_elo(first), self.team_elo(second))
        return self.score_sigmoid(ratings[1] - ratings[0])

    def true_score(self, first: TeamResult, second: TeamResult) -> float:
        return first.points / (first.points + second.points)

    def match_delta(self, match: Match) -> dict[str, float]:
        deltas = {}
        for t in (0, 1):
            for player in match.teams[t]:
                pred = self.pred_score(match.teams[t], match.teams[1-t])
                true = self.true_score(match.results[t], match.results[1-t])
                delta = self.elo_gain_coef * max(match.points) * (true - pred)
                player_delta = delta * self.player_team_weight(player, match.teams[t])
                deltas[player] = self.free_elo_gain + player_delta
        return deltas

    def score_match(self, match: Match) -> RankingSystem:
        for player in match.players:
            self.elo.setdefault(player, self.initial_elo)
        for player, delta in self.match_delta(match).items():
            self.elo[player] += delta
        self.match_history.append(match)
        return self

    def score_matches(self, matches: Iterable[Match]) -> RankingSystem:
        for match in matches:
            self.score_match(match)
        return self


def main():
    import requests
    key = "1ijei0ZhIdPiY_TazfB2JZAAoNi3CWowgPquQuLv3oSU"
    sheet_name = "games"
    csv_url = f"https://docs.google.com/spreadsheets/d/{key}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    result = requests.get(url=csv_url)
    matches = []
    for row in csv.DictReader(io.StringIO(result.content.decode())):
        teams = tuple(tuple(row[f'team_{i}_player_{j}'] for j in (1, 2, 3)
                            if row[f'team_{i}_player_{j}'])
                      for i in (1, 2))
        scores = int(row['team_1_score']), int(row['team_2_score'])
        match = Match((TeamResult(teams[0], scores[0]), TeamResult(teams[1], scores[1])))
        matches.append(match)
    system = RankingSystem(matches)
    for player, elo in system.ranking:
        print(f"{player: <18} {elo:.3f}")


if __name__ == '__main__':
    main()