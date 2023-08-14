import pandas as pd
import numpy as np
import datetime
import pytz
from Store_Monitoring.Reporter.getData import getData
import logging

FORMAT = (
    "%(asctime)s %(filename)s->%(funcName)s():%(lineno)s %(levelname)s: %(message)s \n"
)
logging.basicConfig(format=FORMAT, level=logging.INFO)


class Reporter:
    """
    Reporter Class calculates the report for each store. Using Store Status data.
    """

    def __init__(self, store_id, current_time):
        self.store_id = store_id
        self.current_time = current_time
        self.get_data = getData()

    def convert_timezone_dataframe(self, dataframe, timezone):
        """
        Converts data UTC timezone to given timezone, for a whole table.
        """
        dataframe["timestamp_local"] = dataframe["timestamp_utc"].apply(
            self.change_timezone, timezone=timezone
        )
        return dataframe

    def change_timezone(self, timestamp, timezone):
        """
        Converts data UTC timezone to given timezone, for a timestamp. Used by convert_timezone_dataframe
        """
        timestamp = datetime.datetime.fromtimestamp(timestamp)

        old_timezone = pytz.timezone("UTC")
        new_timezone = pytz.timezone(timezone)

        localized_timestamp = old_timezone.localize(timestamp)
        new_timezone_timestamp = localized_timestamp.astimezone(new_timezone)

        return new_timezone_timestamp

    def get_day_list(self, min_day, max_day):
        """
        Get's all the list of days between the interval
        """
        day_list = []
        temp_day = max_day
        while temp_day.date() != min_day.date():
            day_list.append(temp_day)
            temp_day = temp_day - datetime.timedelta(days=1)

        return day_list

    def get_beginning_status(self, store_start_time_local, interval_start_time_local):
        """
        After the start of the store, when our interval starts the latest status of the store
        is fetched by this function.
        """
        table = self.get_data.recieve_data_from_store_status(
            store_start_time_local.timestamp(),
            interval_start_time_local.timestamp(),
            self.store_id,
        )
        if len(table) == 0:
            return "open"

        return table["status"].iloc[-1]

    def add_activity_prompt(
        self,
        day_list,
        interval_start_time_local,
        interval_end_time_local,
        dataframe,
        timezone,
    ):
        """
        Adds Open and close timings to the data, so that uptime and downtime can be calculated easily.
        """
        for day in reversed(day_list):
            store_hours = self.get_data.recieve_data_from_menu_hours(
                self.store_id, day.weekday()
            )

            for intervals in store_hours:
                store_start_time_local = datetime.datetime.strptime(
                    f"""{day.strftime("%Y-%m-%d")} {intervals[0]}""",
                    "%Y-%m-%d %H:%M:%S",
                )
                store_start_time_local = pytz.timezone(timezone).localize(
                    store_start_time_local
                )

                store_end_time_local = datetime.datetime.strptime(
                    f"""{day.strftime("%Y-%m-%d")} {intervals[1]}""",
                    "%Y-%m-%d %H:%M:%S",
                )
                store_end_time_local = pytz.timezone(timezone).localize(
                    store_end_time_local
                )

                if (store_start_time_local >= interval_start_time_local) & (
                    store_start_time_local <= interval_end_time_local
                ):
                    ## If store opens in the given interval add time of opening which will be considered active.
                    entry = {
                        "status": ["open"],
                        "timestamp_local": [store_start_time_local],
                    }
                    dataframe = pd.concat(
                        [dataframe, pd.DataFrame(entry)], ignore_index=True
                    )

                elif (store_start_time_local < interval_start_time_local) & (
                    interval_start_time_local < store_end_time_local
                ):
                    ## If store opens before our interval starts, we need to find out the beginning status of the store, before our interval begins
                    beginning_status = self.get_beginning_status(
                        store_start_time_local, interval_start_time_local
                    )
                    entry = {
                        "status": [beginning_status],
                        "timestamp_local": [interval_start_time_local],
                    }
                    dataframe = pd.concat(
                        [dataframe, pd.DataFrame(entry)], ignore_index=True
                    )

                entry = {
                    "status": ["closed"],
                    "timestamp_local": [store_end_time_local],
                }

                dataframe = pd.concat(
                    [dataframe, pd.DataFrame(entry)], ignore_index=True
                )

        dataframe = dataframe.sort_values(by="timestamp_local")
        return dataframe

    def get_report_abstract(self, start_time, end_time):
        """
        get_report_abstract gets the timeframe and provides the uptime and downtime for the class store.
        """
        table = self.get_data.recieve_data_from_store_status(
            start_time.timestamp(), end_time.timestamp(), self.store_id
        )

        timezone = self.get_data.recieve_data_from_timezone(self.store_id)
        start_time_local = self.change_timezone(start_time.timestamp(), timezone)
        end_time_local = self.change_timezone(end_time.timestamp(), timezone)

        days_list = self.get_day_list(start_time_local, end_time_local)

        table = self.convert_timezone_dataframe(table, timezone)
        table = self.add_activity_prompt(
            days_list, start_time_local, end_time_local, table, timezone
        )

        uptime, downtime = self.get_uptime_downtime(table)

        return uptime, downtime

    def get_last_hour_report(self):
        """
        Get uptime and downtime for last hour (60 minutes from current timestamp).
        """
        end_time = self.current_time
        start_time = end_time - datetime.timedelta(seconds=3600)  ## one hour
        uptime, downtime = self.get_report_abstract(start_time, end_time)

        return uptime / 60, downtime / 60  ## in minutes

    def get_last_day_report(self):
        """
        Get uptime and downtime for last day (24 hours from current timestamp).
        """
        end_time = self.current_time
        start_time = end_time - datetime.timedelta(seconds=3600 * 24)  ## one day
        uptime, downtime = self.get_report_abstract(start_time, end_time)

        return uptime / 3600, downtime / 3600  ## in hours

    def get_last_week_report(self):
        """
        Get uptime and downtime for last week (7*24 hours from current timestamp).
        """
        end_time = self.current_time
        start_time = end_time - datetime.timedelta(seconds=3600 * 24 * 7)  ## one week
        uptime, downtime = self.get_report_abstract(start_time, end_time)

        return uptime / 3600, downtime / 3600  ## in hours

    def get_uptime_downtime(self, table):
        """
        Returns uptime and downtime in seconds
        """
        table_len = len(table)
        i = 0
        uptime = 0
        downtime = 0

        while i < table_len:
            j = i
            if (table["status"].iloc[i] == "active") or (
                table["status"].iloc[i] == "open"
            ):
                while (
                    (j < table_len)
                    and (table["status"].iloc[j] == "active")
                    or (table["status"].iloc[j] == "open")
                ):
                    j += 1
                if j == table_len:
                    uptime += (
                        table["timestamp_local"].iloc[j - 1]
                        - table["timestamp_local"].iloc[i]
                    ).total_seconds()
                else:
                    uptime += (
                        table["timestamp_local"].iloc[j]
                        - table["timestamp_local"].iloc[i]
                    ).total_seconds()

            elif table["status"].iloc[i] == "inactive":
                while j < table_len and table["status"].iloc[j] == "inactive":
                    j += 1

                if j == table_len:
                    downtime += (
                        table["timestamp_local"].iloc[j - 1]
                        - table["timestamp_local"].iloc[i]
                    ).total_seconds()
                else:
                    downtime += (
                        table["timestamp_local"].iloc[j]
                        - table["timestamp_local"].iloc[i]
                    ).total_seconds()

            elif table["status"].iloc[i] == "closed":
                while j < table_len and table["status"].iloc[j] != "open":
                    j += 1

            i = j

        return uptime, downtime
