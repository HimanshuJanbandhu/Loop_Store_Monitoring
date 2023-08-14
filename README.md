# Loop_Store_Monitoring
A take home assignment from Loop that provides API to track activity of stores

# Running Instructions
Follow these instructions to run this on your system

1. Run the following in your command line
```
# Install Requirements
pip install -r requirements.txt

# Start Databases
sudo service mysql start
brew services start mongodb

# Create Databases
python3 Store_Monitoring/DataLoader/mysql_loader.py
python3 Store_Monitoring/DataLoader/mongodb_loader.py
```

2. Once your mysql and mongodb databases are created, up and running. You can run the project using the following command. It will run the ```trigger_report``` and ```get_report``` apis
```
python3 main.py
```