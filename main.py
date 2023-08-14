import pandas as pd
import numpy as np
import datetime

from Store_Monitoring.Reporter.store_monitoring import store_monitoring


def main():
    """
    Creates the Store Monitoring Object which is able to leverage trigger_report and get_report.
    To get the report.
    """
    str_mon = store_monitoring()
    report_id = str_mon.trigger_report(sample=20)  ## 2023, 1, 24
    str_mon.get_report(report_id)


if __name__ == "__main__":
    main()
