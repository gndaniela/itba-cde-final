# pyspark
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib
import tempfile
import boto3

df = pd.read_parquet("s3://itba-tp-02-parquet/output")

df["home_team_index"] = df["home_team"].astype("category").cat.codes
df["away_team_index"] = df["away_team"].astype("category").cat.codes
df["home_team_continent_index"] = df["home_team_continent"].astype("category").cat.codes
df["away_team_continent_index"] = df["away_team_continent"].astype("category").cat.codes

df_base = df.copy()

df = df.drop(
    ["home_team", "away_team", "home_team_continent", "away_team_continent"], axis=1
)

rf = RandomForestClassifier(n_estimators=50, min_samples_split=10, random_state=1)

predictors = [
    "home_team_continent_index",
    "away_team_continent_index",
    "home_team_fifa_rank",
    "away_team_fifa_rank",
    "home_team_total_fifa_points",
    "away_team_total_fifa_points",
    "year",
    "home_team_index",
    "away_team_index",
]

train = df[df["year"] < 2022]
test = df[df["year"] >= 2022]

rf.fit(train[predictors], train["target"])


# Save model

s3_client = boto3.client("s3")
bucket_name = "itba-tp-03-model"
key = "file/model.pkl"

# WRITE
with tempfile.TemporaryFile() as fp:
    joblib.dump(rf, fp)
    fp.seek(0)
    s3_client.put_object(Body=fp.read(), Bucket=bucket_name, Key=key)

# Generate dict df

team_list = [
    "Argentina",
    "Brazil",
    "Ecuador",
    "Uruguay",
    "Australia",
    "Cameroon",
    "Ghana",
    "Morocco",
    "Senegal",
    "Tunisia",
    "IR Iran",
    "Japan",
    "Qatar",
    "Saudi Arabia",
    "Korea Republic",
    "Canada",
    "Costa Rica",
    "Mexico",
    "USA",
    "Belgium",
    "Croatia",
    "Denmark",
    "England",
    "France",
    "Germany",
    "Netherlands",
    "Poland",
    "Portugal",
    "Serbia",
    "Spain",
    "Switzerland",
    "Wales",
]
df_final = df_base[df_base["home_team"].isin(team_list)]
df_final["rank"] = df_final.groupby("home_team")["year"].rank(
    method="first", ascending=False
)
last_info = df_final[df_final["rank"] == 1]
last_info = last_info.loc[
    :, ["home_team", "home_team_fifa_rank", "home_team_total_fifa_points"]
]
df_final.drop("rank", axis=1, inplace=True)


df_home = df_final.loc[
    :,
    [
        "home_team_index",
        "home_team",
        "home_team_continent_index",
        "home_team_continent",
    ],
]
df_away = df_final.loc[
    :,
    [
        "away_team_index",
        "away_team",
        "away_team_continent_index",
        "away_team_continent",
    ],
]
df_dict = pd.merge(df_home, df_away, left_on="home_team", right_on="away_team").drop(
    ["away_team", "away_team_continent"], axis=1
)
df_dict.rename(
    columns={"home_team": "team", "home_team_continent": "continent"}, inplace=True
)

df_dict = df_dict.loc[
    :,
    [
        "team",
        "continent",
        "home_team_index",
        "away_team_index",
        "home_team_continent_index",
        "away_team_continent_index",
    ],
]


df_dict = pd.merge(df_dict, last_info, left_on="team", right_on="home_team").drop(
    "home_team", axis=1
)
df_dict.rename(
    columns={
        "home_team_fifa_rank": "fifa_rank",
        "home_team_total_fifa_points": "fifa_points",
    },
    inplace=True,
)

print(df_dict.head())

# Save dict
s3_url = "s3://itba-tp-02-parquet/clean/df_dict.parquet"
df_dict.to_parquet(s3_url)
