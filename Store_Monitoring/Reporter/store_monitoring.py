import pandas as pd
import numpy as np
import datetime
from Store_Monitoring.Reporter.getData import getData
from Store_Monitoring.Reporter.reporter import Reporter
from Store_Monitoring.DataLoader.mysql_loader import (
    create_connection,
    execute_query,
    create_database_connect,
    create_table,
)
from tqdm import tqdm
import logging

FORMAT = (
    "%(asctime)s %(filename)s->%(funcName)s():%(lineno)s %(levelname)s: %(message)s \n"
)
logging.basicConfig(format=FORMAT, level=logging.INFO)


class store_monitoring:
    """
    Store Monitoring provides the report on all the stores
    """

    def __init__(self):
        get_data_obj = getData()
        onboarded_df = get_data_obj.get_stores_onboarded()
        self.stores_onboarded = list(onboarded_df["store_id"])
        DB_connect = create_connection()
        store_monitoring_connect = create_database_connect(
            DB_connect, "store_monitoring"
        )
        self.MySQL_DB_connect = store_monitoring_connect

    def trigger_report(self, sample=None):
        """
        This function triggers the creation of the report.
        If you provide sample (int) it will only run on first {sample} stores.
        """
        report = pd.DataFrame(
            columns=[
                "store_id",
                "uptime_last_hour(in minutes)",
                "uptime_last_day(in hours)",
                "uptime_last_week(in hours)",
                "downtime_last_hour(in minutes)",
                "downtime_last_day(in hours)",
                "downtime_last_week(in hours)",
            ]
        )

        logging.info("triggering report")
        if sample is not None:
            store_list = self.stores_onboarded[:sample]
        else:
            store_list = self.stores_onboarded

        for store in tqdm(store_list):
            logging.info(store)
            report_obj = Reporter(store, datetime.datetime.now())
            uptime_last_hour, downtime_last_hour = report_obj.get_last_hour_report()
            uptime_last_day, downtime_last_day = report_obj.get_last_day_report()
            uptime_last_week, downtime_last_week = report_obj.get_last_week_report()
            report_entry = {
                "store_id": [store],
                "uptime_last_hour(in minutes)": [uptime_last_hour],
                "uptime_last_day(in hours)": [uptime_last_day],
                "uptime_last_week(in hours)": [uptime_last_week],
                "downtime_last_hour(in minutes)": [downtime_last_hour],
                "downtime_last_day(in hours)": [downtime_last_day],
                "downtime_last_week(in hours)": [downtime_last_week],
            }

            report = pd.concat([report, pd.DataFrame(report_entry)], ignore_index=True)

        if sample is not None:
            report_id = (
                f"Sample_{sample}_Report_"
                + f"{int(datetime.datetime.now().timestamp())}"
            )
        else:
            report_id = "Report_" + f"{int(datetime.datetime.now().timestamp())}"
        report["report_id"] = report_id

        create_table(
            "store_monitoring", "store_monitoring_report", report, if_exists="append"
        )

        logging.info("Report Completed")

        return report_id

    def get_report(self, report_id):
        """
        Gets the report corressponding to the report_id, from the DB. If the report is not present
        then returns Running.
        """
        query = f"""SELECT * FROM store_monitoring_report 
                    WHERE report_id = "{report_id}" """

        res = execute_query(self.MySQL_DB_connect, query)
        table = pd.DataFrame(
            res.fetchall(), columns=[desc[0] for desc in res.description]
        )
        if len(table) == 0:
            logging.info("Running")
            return "Running"

        report_name = f"Reports/{report_id}_report.csv"
        table.to_csv(report_name)
        logging.info("Complete")
        return report_name
