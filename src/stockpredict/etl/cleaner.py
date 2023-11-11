import argparse
import logging

from stockpredict.etl.preprocess import Preprocess
from pyspark.sql import SparkSession, DataFrame, functions as F, Window

from stockpredict.settings import NETWORK_OUT_LABELS


def normalize(df: DataFrame) -> DataFrame:
    ### IQR normalization
    """ Calculate the first quartile (Q1) and the third quartile (Q3) of your dataset.
        Calculate the interquartile range (IQR) as IQR = Q3 - Q1.
        For each data point xi, calculate its normalized value using the formula:
        iqr_normalized(xi) = (xi - Q1) / IQR
    """

    columns = df.columns

    p_25 = "{key}_percent_25"
    p_75 = "{key}_percent_75"

    df = (df.withColumn("partkey", F.lit(1))
    .withColumns(
        {
            **{p_25.format(key=key): F.percentile_approx(F.col(key), .25).over(Window().partitionBy("partkey")) for key in columns if key not in NETWORK_OUT_LABELS},
            ** {p_75.format(key=key): F.percentile_approx(F.col(key), .75).over(Window().partitionBy("partkey")) for key in columns if key not in NETWORK_OUT_LABELS}

        }
    ).withColumns({
        **{key: (F.col(key) - F.col(p_25.format(key=key))) / (F.col(p_75.format(key=key)) -  F.col(p_25.format(key=key))) for key in columns if key not in NETWORK_OUT_LABELS}
    })).drop(*[p_25.format(key=key) for key in columns if key not in NETWORK_OUT_LABELS], *[p_75.format(key=key) for key in columns if key not in NETWORK_OUT_LABELS])

    df = df.fillna(0.0)

    return df


def save(df: DataFrame, path: str) -> None:
    df.write.format("delta").save(path=path, mode="overwrite")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_data")
    parser.add_argument("--output_data")

    args = parser.parse_args()
    logging.info(args.output_data)
    logging.info(args.input_data)

    logging.info("starting flow")
    spark = SparkSession.builder.getOrCreate()

    data = Preprocess(spark, args.input_data).execute()

    normalized = normalize(data)
    save(normalized, args.output_data)

    logging.info("finished flow")
