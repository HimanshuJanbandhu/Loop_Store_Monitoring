from pymongo import MongoClient
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import os
import sys

PATH = os.path.dirname(os.path.abspath(sys.argv[0]))


def get_database(db_name):
    CONNECTION_STRING = "mongodb://localhost:27017/"
    client = MongoClient(CONNECTION_STRING)

    return client[db_name]


def get_collection(db, collection_name):
    return db[collection_name]


def add_items_to_collection(collection, items):
    collection.insert_many(items)


def main():
    menu_hours_df = pd.read_csv(PATH + "/Menu_hours.csv")

    timezone_df = pd.read_csv(PATH + "/bq-results-20230125-202210-1674678181880.csv")

    store_monitoring = get_database("store_monitoring")

    menu_hours = get_collection(store_monitoring, "menu_hours")
    menu_hours.delete_many({})
    add_items_to_collection(menu_hours, menu_hours_df.to_dict("records"))

    timezone = get_collection(store_monitoring, "timezone")
    timezone.delete_many({})
    add_items_to_collection(timezone, timezone_df.to_dict("records"))

    myquery = {"store_id": 1481966498820158979}
    mydoc = timezone.find(myquery)
    print(mydoc)
    for x in mydoc:
        print(x)


if __name__ == "__main__":
    main()
