import mysql.connector as connection
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime
import os
import sys
from urllib.parse import quote

PATH = os.path.dirname(os.path.abspath(sys.argv[0]))
password = "Asd123@#"
host = "localhost"
user = "root"


def create_connection():
    try:
        DB_connect = connection.connect(
            host=host,
            user=user,
            password=password,
        )
    except Exception as e:
        print(e)

    return DB_connect


def execute_query(DB_connect, query):
    Cursor = DB_connect.cursor()
    Cursor.execute(query)
    return Cursor


def create_database_connect(DB_connect, name):
    query = f"CREATE DATABASE IF NOT EXISTS {name}"

    execute_query(DB_connect, query)

    DB_connect = connection.connect(
        host="localhost", user="root", password=password, database=name
    )

    return DB_connect


def create_table(DB_name, table_name, dataframe, if_exists="replace"):
    engine = create_engine(
        "mysql+pymysql://{user}:%s@{host}/{db}".format(host=host, db=DB_name, user=user)
        % quote(password)
    )

    dataframe.to_sql(table_name, engine, index=False, if_exists=if_exists)


def store_status_cleaning(store_status_df):
    def convert_to_epochtime(x):
        for format in ("%Y-%m-%d %H:%M:%S.%f UTC", "%Y-%m-%d %H:%M:%S UTC"):
            try:
                return int(datetime.strptime(x, format).strftime("%s"))
            except ValueError:
                pass

    store_status_df["timestamp_utc"] = store_status_df["timestamp_utc"].apply(
        convert_to_epochtime
    )
    return store_status_df


def print_table(cursor):
    result = cursor.fetchall()
    for row in result:
        print(row)


def main():
    DB_connect = create_connection()
    DB_name = "store_monitoring"
    DB_connect = create_database_connect(DB_connect, DB_name)

    table_name = "store_status"

    dataframe = pd.read_csv(PATH + "/store_status.csv")
    dataframe = store_status_cleaning(dataframe)

    create_table(DB_name, table_name, dataframe)

    menu_hours_df = pd.read_csv(PATH + "/Menu_hours.csv")

    create_table(
        DB_name,
        "universal_store_list",
        pd.DataFrame({"store_id": menu_hours_df["store_id"].unique()}),
    )

    query = f"SELECT * FROM universal_store_list LIMIT 5"
    cursor = execute_query(DB_connect, query)
    print_table(cursor)


if __name__ == "__main__":
    main()
