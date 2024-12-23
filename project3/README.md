# README

## CODE Overview
This system is designed for continuous data collection and analysis of hate speech content from 4chan and Reddit using Faktory job queues, Docker containers, and PostgreSQL for storing data. The code consists of several components that handle data crawling, job scheduling, and visualization generation.

Crawling Functions: (crawler.py)

crawl_4chan(): Collects thread data from 4chan by interacting with the ChanClient object and pushes it to the Faktory queue.
crawl_reddit(): Collects subreddit data from Reddit using the RedditClient object and pushes it to the Faktory queue.
Works as a scheduler for future jobs

Clients: 

clients->ChanClient : Contains the ChanClient object responsible for interacting with 4chan and batch ingesting data.
client_reddit->RedditClient : Contains the RedditClient object responsible for interacting with Reddit and batch ingesting data.
Both objects are used in the crawler.py file, where they handle the batch ingestion of data by hitting the APIs of 4chan, Reddit, and HATESPEECH.

plot_data(): Generates visualizations of the collected data using the visualize() function and schedules the job for plotting in the Faktory queue.

Furthermore, as discussed earlier, we have separate files for 4Chan and Reddit clients. By maintaining separate process queues for 4Chan and Reddit, robustness is ensured even if one of them goes down.

 
## Initialize the SETUP by Pulling and Running Docker Container for PostgreSQL

First, pull the Docker container for TimescaleDB:

```sh
docker pull timescale/timescaledb-ha:pg16
```

Run the Docker container:

```sh
docker run -d --name timescaledb -p 5432:5432 -e POSTGRES_PASSWORD=testpassword timescale/timescaledb-ha:pg16
```

- **Database Used:** `postgres`
- **Connection URL:** `DATABASE_URL='postgres://postgres:testpassword@localhost:5432/postgres'`

## Pull and Run Docker Container for Faktory

Pull the Docker container for Faktory:

```sh
docker pull contribsys/faktory
```

Run the Docker container:

```sh
docker run -it --name faktory \
  -v ~/projects/docker-disks/faktory-data:/var/lib/faktory/db \
  -e "FAKTORY_PASSWORD=password" \
  -p 127.0.0.1:7419:7419 \
  -p 127.0.0.1:7420:7420 \
  contribsys/faktory:latest \
  /faktory -b :7419 -w :7420
```

## Setup Required Tables and Schema

Before initializing the script, setup the required tables and schema. Run the following command:

```sh
sudo docker exec -i timescaledb psql -U postgres < <project_path>/script.sql
```
> **Note:** An additional table named toxic_table is created in this file to handle the hatespeech data ingestion from 4chan and Reddit
> **Note:** It also alters the subreddit_table to add an extra column is_comment for additional analysis 


## Create Virtual Environment

Create a virtual environment in the `env` folder:

```sh
python3 -m venv env/
```

Activate the virtual environment:

```sh
source env/bin/activate
```

## Install Required Libraries

Install all necessary libraries:

```sh
pip install -r requirements.txt
```

> **Note:** You don't need to activate the virtual environment each time you log in to the server. The `run_crawler.sh` script will handle activation automatically when called.

## Edit Configuration File

Edit the `.cfg` file to set dynamic configurations such as URLs, 4chan boards, Subreddits, and other server settings.

## Run the Data Collection System

# Note: If the logs files not present in the 'logs' folder, create the empty files using 

```sh
touch Reddit.log
touch 4Chan.log
```

Finally, run the continuous polling script:

```sh
./run_crawler.sh <proj_dir_name>
```
## The application spawns multiple process based on configurations ensures efficient Crawling! 🕷️

Stay informed and up-to-date with the latest trends in technology 💻, politics 🗳️, and hate speech across subreddits and 4chan. If you encounter any issues or need further assistance, feel free to reach out. Enjoy your data collection journey! 🚀


## The Technology Analysis Dashboard

The Technology Analysis Dashboard is developed using Flask in python3

Script.js: 1- This file ensures that the data fetching logic and chart updating logic is error-free and handles asynchronous    operations correctly.
2-Improve readability and maintainability by separating concerns into smaller functions where possible. 

index.html: 1-Make sure the layout is user-friendly and that elements are correctly linked.

app.py: This is the main file that runs the flask engine and executes the end-points 

TO Run the Flask app:
Step 1: Open a new terminal and activate env using the command: 

```sh
source env/bin/activate
```

Step 2: Run The Flask App with the command: 

```sh
pythont3 app.py
```

The Application should be up and running on http://127.0.0.1:5000/



