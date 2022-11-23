#pyspark
import sys
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import IntegerType

sc = SparkContext()
spark = SparkSession(sc)
spark.conf.set("spark.sql.sources.partitionOverwriteMode","dynamic")


def parse_csv_parquet(source, dest):
    # read input
    df = spark.read.option("header", True).csv(source)
    # custom columns and wrangling
    df = df.withColumn("target",when(col('home_team_result')=='Win',1).otherwise(0))\
                           .withColumn("year",year(col('date')))\
                           .withColumn("home_team_fifa_rank",df.home_team_fifa_rank.cast(IntegerType()))\
                           .withColumn("away_team_fifa_rank",df.away_team_fifa_rank.cast(IntegerType()))\
                           .withColumn("home_team_total_fifa_points",df.home_team_total_fifa_points.cast(IntegerType()))\
                           .withColumn("away_team_total_fifa_points",df.away_team_total_fifa_points.cast(IntegerType()))\
                           .withColumn("home_team_score",df.home_team_score.cast(IntegerType()))\
                           .withColumn("away_team_score",df.away_team_score.cast(IntegerType()))\
                           .drop('city','country','shoot_out','date','tournament','neutral_location','away_team_goalkeeper_score','home_team_mean_defense_score','home_team_goalkeeper_score',\
                                 'home_team_mean_offense_score','home_team_mean_midfield_score','away_team_mean_defense_score','away_team_mean_offense_score','away_team_mean_midfield_score','home_team_result',\
                                 'home_team_score','away_team_score')

    # save as parquet
    df.write.mode("overwrite").format("parquet").save(dest)

if __name__ == "__main__":
    parse_csv_parquet("s3://itba-tp-01-raw-csv/","s3://itba-tp-02-parquet/output")
