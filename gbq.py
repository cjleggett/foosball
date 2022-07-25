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

query_string = "SELECT * FROM qc-foosball-analytics-dev.foosball.match_history LIMIT 1000"

print("a")

temp = bqclient.query(query_string).result()

print(temp)

dataframe = (
    bqclient.query(query_string)
    .result()
    .to_dataframe(
        create_bqstorage_client=False,
    )
)

print("b")

print(dataframe.head())


def write_rows():
    df = DataFrame({"team0_score": [0], "team1_score": [10], "team0_players": ["['Joe']"], "team1_players": ["['Doe']"], "game_timestamp": [datetime.utcnow()]})
    df.to_gbq("foosball.match_history", if_exists="append")


write_rows()