# Loop_Store_Monitoring
A take home assignment from Loop that provides API to track activity of stores

# Running Instructions
Follow these instructions to run this on your system

1. Run the following in your command line
```
# Install Requirements
pip install -r requirements.txt
```
2. Add store_status.csv to ```Store_Monitoring/DataLoader/```

3. Run the following in your command line
```
# Start Databases
sudo service mysql start
brew services start mongodb

# Create Databases
python3 Store_Monitoring/DataLoader/mysql_loader.py
python3 Store_Monitoring/DataLoader/mongodb_loader.py
```

4. Once your mysql and mongodb databases are created, up and running. You can run the project using the following command. It will run the ```trigger_report``` and ```get_report``` apis
```
python3 main.py
```
# Working Explained
## Assumptions
1. Whenever a store opens it will be considered active until we get a inactive status.
2. Whenever we get a active status from a store it will be active until eitheir it's closed or we get a inactive status.
3. Whenever we get a inactive status from a store it will be inactive until eitheir it's closed or we get a active status.

## Working
### Storing data
1. Store_status table is stored in a mysql DB by the name store_status.
2. Menu_Hours and Timezone is stored in mongoDB by the name menu_hours and timezone repectively.
3. A list of stores from Menu_hours is stored in mysql DB by the name universal_store_list.

### Calculation of uptime and downtime
1. We calculate report for each store individually.
2. We filter the tale for the time interval report is required. (For example, one table for last_hour, another for last_day and so on.)
3. We convert the table UTC timezone to local timezone. Hence now the enteries in this filtered ```store_status``` table are in local timezone of that store.
4. After Filtering, We add where the store is open and closed
5. The sequence from the table might look like this

#### Case 1

- `interval_starts`
- store_open
- active
- active
- store_closed
- active
- inactive
- active
- store_open
- active
- inactive
- closed
- `interval_closed`

or

#### Case 2

- store_open
- active
- `interval_starts`
- store_closed
- active
- inactive
- active
- store_open
- active
- inactive
- closed
- `interval_closed`

#### Case 1
- For this case we add the times where store was open and closed and then sort the whole table (based on local timezone datetime), so that we get a linear timeline in the table.
#### Case 2
- For this case we again fetch the ```store_status``` table from store_open timing to interval_start timing and find the latest status of the store and add that to the table.

6. Now we calculate the uptime and downtime.
- We start from the top of the table
    - if the status is open or active, we calculate uptime until store is closed or inactive.
    - if the status is inactive, we calculate downtime until store is closed or active.
    - if the status is closed, we move forward in the table till we find open.

7. Hence, for every store uptime and downtime is calculated for last_hour, last_day and last_week.

## Unclear
1. When we are talking about last hour 
Do we consider 60 mins from this second or the last hour altogether.
Similar argument can be made about day and week.

2. What to do about the status that we recieve when the restaurent in closed. Is it relevant, do we need to use it?

# Improvements
There are still some improvements that can be made, but due to constraints on time I wasn't able to implement,

1. Code quality - One thing that can be improved is that whereever constants are being used, they should be stored in a seperate file, hence it will be easier to access.

2. Algorithm - While calculation of uptime and downtime,
- When we are on a active timestamp, we are looking for next inactive or closed
- When we are on a inactive timestamp, we are looking for next active
- When we are on a closed timestamp, we are looking for next inactive
 
These can also be implemented using binary search, however due to time constraint I wasn't able to test it, but this can be improved.