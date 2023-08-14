import pandas as pd
import numpy as np

from Store_Monitoring.DataLoader.mysql_loader import (
    create_connection,
    execute_query,
    create_database_connect,
)
from Store_Monitoring.DataLoader.mongodb_loader import get_database, get_collection


class getData:
    def __init__(self) -> None:
        DB_connect = create_connection()
        store_monitoring_connect = create_database_connect(
            DB_connect, "store_monitoring"
        )
        self.MySQL_DB_connect = store_monitoring_connect
        self.Mongo_DB_connect = get_database("store_monitoring")

    def get_stores_onboarded(self):
        query = """SELECT * FROM universal_store_list"""
        res = execute_query(self.MySQL_DB_connect, query)
        table = pd.DataFrame(
            res.fetchall(), columns=[desc[0] for desc in res.description]
        )

        return table

    def recieve_data_from_store_status(self, start_time, end_time, store_id):
        query = f"""SELECT status,timestamp_utc FROM store_status 
                WHERE timestamp_utc >= {start_time} AND timestamp_utc <= {end_time} AND store_id = {store_id}"""

        res = execute_query(self.MySQL_DB_connect, query)
        table = pd.DataFrame(
            res.fetchall(), columns=[desc[0] for desc in res.description]
        )
        return table

    def recieve_data_from_timezone(self, store_id):
        timezone_collection = get_collection(self.Mongo_DB_connect, "timezone")
        query = {"store_id": store_id}

        timezone_res = timezone_collection.find(query)
        timezone_str = ""
        for i in timezone_res:
            timezone_str = i["timezone_str"]

        if timezone_str == "":
            return "America/Chicago"

        return timezone_str

    def recieve_data_from_menu_hours(self, store_id, day):
        menu_hours_collection = get_collection(self.Mongo_DB_connect, "menu_hours")
        query = {"store_id": store_id, "day": day}

        documents = menu_hours_collection.find(query)
        menu_hours_local = []

        for doc in documents:
            menu_hours_local.append([doc["start_time_local"], doc["end_time_local"]])

        if len(menu_hours_local) == 0:
            menu_hours_local.append(["00:00:00", "23:59:59"])

        return menu_hours_local
