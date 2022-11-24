import logging
from flask import Flask, request, session, render_template, url_for, redirect
import builtins as p
import pandas as pd
import tempfile
import boto3
import joblib
import pymysql

# DB
import dbconnect as db

# Logging
logging.basicConfig(
    filename="error.log",
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

app = Flask(__name__)

app.secret_key = "B!1w8NAt1T^%kvhUI*S^"

# read dict table
df_dict = pd.read_parquet("s3://itba-tp-02-parquet/clean/df_dict.parquet")

# reload model
s3_client = boto3.client("s3")
bucket_name = "itba-tp-03-model"
key = "file/model.pkl"

with tempfile.TemporaryFile() as fp:
    s3_client.download_fileobj(Fileobj=fp, Bucket=bucket_name, Key=key)
    fp.seek(0)
    rf = joblib.load(fp)


@app.route("/")
def home():
    teams = [
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
    teams.sort()
    return render_template("index.html", teams=teams)


@app.route("/predict", methods=["GET", "POST"])
def predict():
    teamhost = request.form["teamhost"]
    teamaway = request.form["teamaway"]

    app.logger.info(f"{teamhost} vs {teamaway}")

    home_team_continent_index = (
        df_dict[df_dict["team"] == teamhost]["home_team_continent_index"]
        .reset_index()
        .iloc[0]["home_team_continent_index"]
    )
    away_team_continent_index = (
        df_dict[df_dict["team"] == teamaway]["away_team_continent_index"]
        .reset_index()
        .iloc[0]["away_team_continent_index"]
    )
    home_team_fifa_rank = (
        df_dict[df_dict["team"] == teamhost]["fifa_rank"]
        .reset_index()
        .iloc[0]["fifa_rank"]
    )
    away_team_fifa_rank = (
        df_dict[df_dict["team"] == teamaway]["fifa_rank"]
        .reset_index()
        .iloc[0]["fifa_rank"]
    )
    home_team_total_fifa_points = (
        df_dict[df_dict["team"] == teamhost]["fifa_points"]
        .reset_index()
        .iloc[0]["fifa_points"]
    )
    away_team_total_fifa_points = (
        df_dict[df_dict["team"] == teamaway]["fifa_points"]
        .reset_index()
        .iloc[0]["fifa_points"]
    )
    home_team_index = (
        df_dict[df_dict["team"] == teamhost]["home_team_index"]
        .reset_index()
        .iloc[0]["home_team_index"]
    )
    away_team_index = (
        df_dict[df_dict["team"] == teamaway]["away_team_index"]
        .reset_index()
        .iloc[0]["away_team_index"]
    )

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

    data = [
        {
            "home_team_continent_index": int(home_team_continent_index),
            "away_team_continent_index": int(away_team_continent_index),
            "home_team_fifa_rank": int(home_team_fifa_rank),
            "away_team_fifa_rank": int(away_team_fifa_rank),
            "home_team_total_fifa_points": int(home_team_total_fifa_points),
            "away_team_total_fifa_points": int(away_team_total_fifa_points),
            "year": 2022,
            "home_team_index": int(home_team_index),
            "away_team_index": int(away_team_index),
        }
    ]

    pred_df = pd.DataFrame(data)

    result = rf.predict(pred_df[predictors])
    proba = rf.predict_proba(pred_df[predictors])
    result = result[0]
    proba = max(proba[0])
    proba = p.round(proba.item() * 100, 2)

    session["proba"] = int(proba)
    session["result"] = int(result)

    app.logger.info(f"{result} vs {proba}%")

    if result == 0:
        app.logger.info(f"Home team loses: {proba}%")
    else:
        app.logger.info(f"Home team wins: {proba}%")

    # insert in db
    app.logger.info("Insert in DB")
    db.insert_row(teamhost, teamaway)
    return render_template(
        "predict.html",
        proba=session.get("proba"),
        result=session.get("result"),
        teamhost=teamhost,
        teamaway=teamaway,
    )


if __name__ == "__main__":
    app.run(debug=True)
