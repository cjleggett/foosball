# Dependencies (conda):
# conda-forge google-cloud-bigquery
# google-cloud-bigquery-storage
# pandas
# pandas-gbq
# pyarrow

# Also set the env variable GOOGLE_APPLICATION_CREDENTIALS to the path of the key JSON you can create and download here:
# https://console.cloud.google.com/iam-admin/serviceaccounts/details/108628258820199466140/keys?project=qc-foosball-analytics-dev&supportedpurview=project

from google.cloud import bigquery
from pandas import DataFrame
from datetime import datetime


bqclient = bigquery.Client()


def write_rows(team0_score, team0_players, team1_score, team1_players):
    df = DataFrame({"team0_score": [team0_score], "team1_score": [team1_score],
                    "team0_players": [team0_players], "team1_players": [team1_players],
                    "game_timestamp": [datetime.utcnow()]})
    df.to_gbq("foosball.match_history", if_exists="append")
