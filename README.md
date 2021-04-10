![Screen Shot 2021-04-09 at 4 39 00 PM](https://user-images.githubusercontent.com/6299223/114250298-20b47f00-9952-11eb-837f-9976bb998376.png)
# ABOUT THE PROJECT
<details open>
<summary>About the Project</summary>
        
TC2 is the Python edition of my original TradeCatcher Java project, carefully rewritten and designed to make it as quick as possible to 
implement new strategies and technical analysis models, optimize the strategies and models, and visualize them.

Additionally, TC2 includes a webpanel that enables more precise control of the program's operations.
</details>


# HOW THE PROGRAM WORKS
<details>
<summary>Deployment Frameworks</summary>
        
The program is contained within a few docker containers:
- Redis database for storing backend program data (port 6379)
- MongoDB database for storing stock market data (port 27017)
- PostgreSQL database for storing frontend program data (port 5432)
- Python 3.7 container for the Django & Gunicorn backend (port 9000)
- NginX container for the Angular 8 frontend (port 9100)

Docker Volumes are used to persist data in the ```TC2_data``` folder, so the entire program can be easily deployed on
 a new machine by simply copying over the contents of this folder.
 
The program is not configured to allow data storage on remote machines, since the network connecting the database
 containers to the program's other containers is firewalled off from the outside world.
</details>


<details>
<summary>Backend Frameworks</summary>
        
The backend is driven by Django. When Django starts up, the program starts running its components in separate
 threads and cores. These components can be accessed by the frontend via the Django API.
</details>


<details>
<summary>Frontend Frameworks</summary>
        
The frontend is powered by Angular 8 and deployed via an NginX web server.
</details>


<details>
<summary>Frontend-Backend Authentication</summary>

Note: This section is for reference only; user should not need to alter low-level authentication code.
        
Angular must authenticate with Django to use its API:
- ```POST http://stocks.maxilie.com:9000/api/token username=admin password=yo&rP@ssw0rd_```
- Pull access token from the JSON response: ```'{"access":"...", "refresh":"..."}'```


The access token can be used for 24 hours. When it expires, repeat the steps above to get a new one.

To use the token, append a header to your queries:
```GET http://stocks.maxilie.com:9000/api/test "Authorization: Bearer <your_access_token>```

To create a new Django user in the system, modify the startup command found in `webpanel/management/commands
/createadminuser.py`.
</details>


<details>
<summary>Multi-Threading</summary>
        
The Django application responds to API requests using worker threads, which have access to the `TC2Program` instance
 and its processes running in separate threads/cores.
        
The TC2 program itself consists of four main *processes*, each running in its own core 
(or in its own thread, if there are insufficient cores available):
- Continuous Data Collection and Daily Analysis Model Training
- Optimization of Strategy Parameters Using Historical Simulations
- Live Day Trading (strategy selection and creation logic only; strategy buy+sell logic is executed in another
 thread, as explained below)
- Live Swing Trading

Additionally, there are a few *threads* managed by the program:
- Data Catch-Up Thread
    - Spawned when the program starts up
    - Collects any missing data going back 30 days
    - Terminates after completing its task, and is not created again until the program restarts
- Startup Task Threads
    - Explicitly defined in ```TC2Program```
    - Spawned when the program starts up
    - Perform miscellaneous one-time tasks, usually experiments or debugging procedures
- Account/Data Streams Thread
    - Listens for Alpaca (live brokerage account) and Polygon (live market data) updates
    - Technically, the streams are listened for on an ```async.io``` event loop within the thread
- Visuals Refresher Thread
    - Routinely updates the visuals cache data (stored in redis) needed to generate up-to-date graphs and charts
- Health Checks Refresher Thread
    - Runs health checks (unit tests) during the night
- Django Worker Threads
    - Spawned by API calls to perform tasks (running simulations, fetching program data, etc.)
- Strategy Execution Threads
    - Spawned by the Live Trading processes when they decide to begin execution of a strategy
</details>


<details>
<summary>Execution Environments</summary>

The ```ExecEnv``` class enables the program to execute the same code in both live and simulated environments, without
 the code "knowing" that its time and data references are being spoofed.
 
Execution environments are also useful for multi-threading, because their variables can be duplicated and used safely
 in another thread or core.
 
A separate ```ExecEnv``` instance is created for every thread the program spawn, but all instances of the same
 ```EnvType``` are assumed to not conflict with each other's data. For example, the live trading thread and data
 collection thread are both ```EnvType.LIVE```, but a thread running a strategy simulation needs to interact with
 temporary, simulated data and time variables, and so the simulation's ```ExecEnv``` is ```EnvType.SIMULATION```.

</details>


<details>
<summary>Mongo Documents</summary>

Reference to an instance of ```MongoManager```  is mediated by an instance of ```ExecEnv``` (see above):

```bash
live_env.mongo().some_method()
```

The ```MongoManager``` instance can tell us all the dates on which we have data for a symbol:

```bash
from tc2.util.data_constants import START_DATE
window_end = date(2030, 1, 1)
dates_on_file = mongo.get_dates_in_range('SPY', START_DATE, window_end)
```

Using the list of dates, we can load the price data for one of them:

```bash
# Load candles for the most recent date on file
day = mongo.load_symbol_day('SPY', dates_on_file[-1])
candles = day.candles
# Candle fields: c.moment, c.open, c.high, c.low, c.close, c.volume
```
</details>


<details>
<summary>Data Analysis & Model Training</summary>
        
1) Add methods to train models and calculate statistics in ```analysis/Analyses.py``` or in other analysis files.
2) Modify ```ModelFeeder.apply_day()``` to call your analysis method(s) from Step 1.
This keeps the analysis up to date with the latest data as it becomes available.
3) Optionally, add a check for the new analysis in the ```is_viable()``` method of an ```AbstractStrategy``` class.
This prevents the strategy from executing when the conditions of your check are not met.
</details>


<details>
<summary>Data Collection</summary>
        
The data collection process is as follows:
- When the program starts up, historical data collection is performed.
- While the markets are open, the current day's data is collected from the ```polygon.io``` livestream.
- When the markets close, the *previous* day's data becomes available from the ```polygon.io``` rest API.
- The program overwrites yesterday's livestream data with rest data, and retrains analysis models on the rest data.
- The program trains analysis models on today's stream data.
</details>


<details>
<summary>Strategy Creation</summary>
        
1) Define a new `Strategy` class by extending the `AbstractStrategy` class.
2) The strategy's optional filter logic can be set by overriding the class's `is_viable` method. This is where we 
do two rounds of non-resource-intensive checks: the first takes no data parameter and queries redis for analyses that 
were performed during data collection, while the second takes the latest 2 hours of data and analyzes it on-the-spot.
3) The strategy's buy and sell logic are set by overriding the `buy_logic` and `sell_logic` methods.
4) Call `strategy.stop_running()` to end execution at any point. Until this is done, buy or sell logic will be 
called on every price update.
5) Set `strategy.bought = True` to signal the Executor to move on to running the strategy's `sell_logic`.
6) Optionally, override the class's `make_execution_result` method to record custom data about executions.
</details>


<details>
<summary>Strategy Execution</summary>
        
Note that live execution is handled by `process/LiveTrader.py` and simulated execution by `process/HistoricalEvaluator`. The below steps are shown only for reference purposes.
1) Before executing, check that `strategy.is_viable()` returns `True`.
2) Create a `VirtualAccount` or `AlpacaAccount` object for the strategy's symbol.
3) Create a `StrategyExecutor` object to run the strategy live, or a `StrategyEvaluator` object to simulate runs.
4) Call `executor.run()` or `evaluator.evaluate()` to begin. The thread will block until execution or evaluation is complete.
</details>

<details>
<summary>Visuals</summary>

Visuals are graphs, charts, and other visual aids that help the admin better understand how the program is behaving (see the Visuals section below).      
</details>

<details>
<summary>Health Checks</summary>
        
Health Checks are unit tests that can be run from the webpanel (see the Health Checks section below). Running a health check tells you whether it passed or failed, and gives useful debug info to explain the result.
</details>


# INITIAL SETUP
<details>
<summary>IDE Setup</summary>
        
Step 1: Clone this project into your favorite python IDE (PyCharm is preferred).

Step 2: Install dependencies into your python environment (in PyCharm this is done via the "Project Interpreter" menu).
        The list of dependencies is found in the `requirements.txt` file.
        
Step 3 (optional): Create a GitHub "personal access token" under GitHub Account Settings -> Developer settings.
        This will enable you to use an access token in place of your password when building the docker container
        (Docker or GitHub might require as a security measure).
</details>

    
<details>
<summary>Server Setup</summary>
        
The application runs in a single Docker container, managed by a user named "stocks" on a machine running Ubuntu 18.01.
Separate MongoDB and Redis containers are also required. These are created, started, and stopped using docker-compose
  (more details below).
 ```bash
 # Uninstall old docker versions
 sudo apt-get remove docker docker-engine docker.io containerd runc docker-compose
 
 # Add the docker repo
 sudo apt update
 sudo apt install \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg-agent \
    software-properties-common
 sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"
   
 # Install docker engine
 sudo apt-get install docker-ce docker-ce-cli containerd.io
 
 # Install docker-compose
 sudo curl -L "https://github.com/docker/compose/releases/download/1.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
 sudo chmod +x /usr/local/bin/docker-compose
 ```
 </details>
 
  
# RUNNING THE PROGRAM
<details>
<summary>Starting Docker-Compose</summary>
A single docker-compose.yml file builds and starts all the backend and frontend containers, in this order:

- A Docker bridge network to host backend communication between containers
- A MongoDB database to store historical price data
- A Redis database to store application data
- A PostgreSQL database to store django data
- A Gunicorn application server to interface between django and the web server
- The TC2 Django project acting as an API to the backend and also running trading and data collection processes
- An NginX web server to interface between the application server and the client's web browser

All of these are created using the project's docker-compose.yml file:
```bash
# Pull the latest docker-compose.yml and move to its directory.
cd /home/stocks && rm -rf TC2 && git clone https://<git_user>:<git_app_password>@github.com/maxilie/TC2 && cd TC2 && cd /home/stocks/TC2
# Stop any already-running containers.
docker-compose down
# Run docker-compose detached.
docker-compose up -d

# To restart everything in a single command:
cd /home/stocks && rm -rf TC2 && git clone https://<git_user>:<git_app_password>@github.com/maxilie/TC2 && cd /home/stocks/TC2 && docker-compose down && docker-compose up -d --build

# To restart only django and TC2 in a single command:
# TODO

# To restart only angular and nginx frontend in a single command:
# TODO
```
</details>


<details>
<summary>Stopping Docker-Compose</summary>

```bash
cd /home/stocks/TC2 && docker-compose down
```
</details>


# DEBUGGING
<details>
<summary>Viewing Logs</summary>
        
To view the logs (possibly missing some uncaught errors), use the webpanel:
- `Runtime Control` tab -> `Console` sub-tab

To view errors, system logs, and Django logs, use Docker:
- `docker logs TC2`

To view more detailed or old logs:
```bash
# Virtually SSH into the container
docker exec -it TC2 /bin/bash
# Install a text editor
apt update && apt install nano -y
# Open the log files
nano logs/live_trading/<timestamp>.txt
nano logs/program/<timestamp>.txt
# Exit the container's virtual terminal
exit
```
</details>


<details>
<summary>Debugging Redis</summary>
        
To get a redis client, run:
```bash
docker run --net TC2-network -it --link redis_container:redis --rm redis redis-cli -h redis -p 6379
        
# Useful commands:
keys *
get <key_name>
hgetall <map_key_name>
lrange <list_key_name> 0 -1
```
</details>


<details>
<summary>Debugging MongoDB</summary>

To get a mongo client, run:
```bash
docker exec -it mongo_container bash

# Useful commands:
mongo -u stocksUser
show dbs
use stocks_LIVE
show collections
db.candle_dates.find()
```

</details>


# STRATEGIES
<details>
<summary>CycleStrategy</summary>
        
Principles Behind the Strategy:
- The greedier and more desirable the offer, the shorter we want to leave it open.
- The safer and more realistic the offer, the longer we want to leave it open.
- When the price dips moderately below baseline, we expect it to return slightly below or above baseline.
- Mitigating downside (with stop orders and analysis filters) makes small profits valuable.

Strategy's Logic:
- Use a limit order to automatically buy when the price dips by about 0.3%.
- Keep a stop order when the price is lower than what we bought it for.
- When the price is close to what we bought it for, cycle through different 5 different sell orders, starting with the most greedy.

Strategy's Analysis Models:
- Dip_10 filter: ensures that the expected drop within 10 minutes after buying is not too strong.
- Dip_45 filter: ensures that the expected drop within 45 minutes after buying is not too strong.
- Volatility filter: ensures that the day spread (highest price minus lowest price) has been at least 1.5% over recent days.
- Momentum filter: ensures that momentum (calculated using the day's first 45 minutes of data) is positive but not so strong  that the price will never dip enough to trigger the strategy's buy order
- Profitability filter: ensures that the average profit of simulated strategy executions is solidly positive.
- Rally filter: ensures that the day is predicted by our neural network to have strong rallies.

</details>

<details>
<summary>ReCycleStrategy</summary>
 
The same logic as CycleStrategy, minus the analysis models and the entry time restriction. ReCycleStrategy can enter from one hour after markets open until one hour before markets close.
</details>

# API
<details>
<summary>Update Endpoint</summary>
        
Restart the backend (unload all python modules, pull the latest code from github, and create a new TC2Program):
- ```/api/update```

</details>

<details>
<summary>Logs Endpoint</summary>
        
Return a list of messages for a specific logfile (excluding the '.txt' extension):
- ```/api/logs/file/?filename=program/2019-01-01_0```

Return a list of names of logfiles for a log feed (excludes the logfeed directory and '.txt' extension):
- ```/api/logs/program_filenames```
- ```/api/logs/trading_filenames```
- ```/api/logs/simulation_filenames```
- ```/api/logs/health_filenames```

Return a list of messages from the most recent logfile for a log feed:
- ```/api/logs/program```
- ```/api/logs/trading```
- ```/api/logs/simulation```
- ```/api/logs/health```

</details>

<details>
<summary>Data Endpoint</summary>

Delete all price data and collect new data from polygon.io (this will take a few days):
- ```/api/data/recollect```

Delete price data and collect new data from polygon.io for only one symbol:
- ```/api/data/recollect?symbol=TXN```

Delete some price data and collect new data from polygon.io:
- ```/api/data/recollect?symbol=TXN?start_date=2018/1/1```

Delete all records of trades attempted and/or made by the program:
- ```/api/data/reset_trade_history```

</details>

# VISUALS
<details>
<summary>About Visuals</summary>
        
Visuals are automatically updated while the program is running. To manually update a visual, use the webpanel,
specifically the ```System Checks``` tab and ```Visuals``` sub-tab.

The webpanel uses two base endpoints of the API internally:
- ```/api/visuals/generate?visual_type=<visual_name>&symbol=...``` updates the cache with the latest data needed to display a given visual (could take several minutes depending on the visual), and
- ```/api/visuals/get?visual_type=<visual_name>&symbol=...``` returns the cached visual data in JSON format.

</details>

<details>
<summary>Price Graph</summary>

A graph of price over time for the given symbol.

visual_type: `PRICE_GRAPH`

Required parameters:
- `symbol`: the symbol to generate a price graph for (e.g. 'AAPL')

</details>

<details>
<summary>Run History</summary>

A chart of profit over date, for the 30 most recent strategy runs.

visual_type: `RUN_HISTORY`

Required parameters:
- `paper`: whether the visual should generate a graph for the paper account or live account (e.g. 'true')

</details>


# HEALTH CHECKS
<details>
<summary>About Health Checks</summary>
        
Health Checks are performed automatically while the program is running. To manually perform one, use the 
webpanel, specifically the ```System Checks``` tab and ```Health Checks``` sub-tab.

The webpanel uses two base endpoints of the API internally:
- ```/api/health_checks/perform?check_type=<check_name>&symbol=...``` performs the check and saves the output, and
- ```/api/health_checks/get?check_type=<check_name>&symbol=...``` returns the output in JSON format.

</details>

<details>
<summary>Dip45 Check</summary>
        
Prints debug messages and run tests on the dip45 analysis model.

check_type: `DIP45`

</details>

<details>
<summary>Model Feeding Check</summary>

Prints debug messages and run tests on the analysis models.

check_type: `MODEL_FEEDING`

</details>

<details>
<summary>Mongo Check</summary>

Prints debug messages and run tests on storing and loading from mongo.

check_type: `MONGO`

</details>

<details>
<summary>Data Check</summary>

Checks for missing or inaccurate data on a symbol.

check_type: `DATA`
Optional parameters:
- `symbol`: the symbol whose data will be checked; defaults to TXN

</details>

<details>
<summary>Simulation Timings Check</summary>

Checks that the program can perform simulations quickly enough.

check_type: `SIMULATION_TIMINGS`

</details>


<details>
<summary>Simulation Output Check</summary>

Prints debug messages for a simulated strategy execution on the most recent market day, and check that the results are realistic.

check_type: `SIMULATION OUTPUT`

Optional parameters:
- `day_date`: the date on which to debug a simulation (e.g. 'YYYY/MM/DD')

</details>
