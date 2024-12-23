import os
from os.path import join, dirname
from dotenv import load_dotenv

class Globals():
    current_dir = dirname(__file__)
    dotenv_path = join(current_dir, '.cfg')
    load_dotenv(dotenv_path)

    CLIENT_ID = os.environ.get("CLIENT_ID")
    SECRET = os.environ.get("SECRET_KEY")
    username = os.environ.get("REDDIT_USERNAME")
    password = os.environ.get("REDDIT_PASSWORD")
    FAKTORY_URL = os.environ.get("FAKTORY_URL")
    REDDIT_BASE = os.environ.get("REDDIT_BASE")
    CHAN_4BASE = os.environ.get("CHAN_4BASE")
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SCHEDULE_TIME= int(os.environ.get("SCHEDULE_TIME"))
    BOARDS = os.environ.get("BOARDS").split(",")
    SUBREDDIT_LIST = os.environ.get("SUBREDDIT_LIST").split(",")
    ENDPOINTS = os.environ.get("ENDPOINTS").split(",")
    HATESPEECH_URL= os.environ.get("HATESPEECH_URL")
    HATESPEECH_TOKEN = os.environ.get("HATESPEECH_TOKEN")
    HATESPEECH_THREESHOLD = float(os.environ.get("HATESPEECH_THREESHOLD")) if os.environ.get("HATESPEECH_THREESHOLD") != "" else 0.9


    global_map = {
        "BOARDS": BOARDS,
        'SUBREDDIT_LIST': SUBREDDIT_LIST,
        "SCHEDULE_TIME":SCHEDULE_TIME
    }

    # after = {'top': 't3_1h09e5m', 'new': 't3_1gxidu8', 'hot': 't3_1gypmus'}

     
