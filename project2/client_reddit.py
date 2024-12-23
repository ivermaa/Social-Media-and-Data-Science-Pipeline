import requests
import json
from dbconnector import DBobj
from globalparams import Globals
# from pyfaktory import Job
import datetime
from datetime import timezone, timedelta
import psycopg2
from psycopg2 import sql
import time
import logging
from collections import deque

db_obj = DBobj()

class RedditClient():
    def __init__(self, logger_name):
        self.API_BASE = Globals.REDDIT_BASE
        self.auth = requests.auth.HTTPBasicAuth(Globals.CLIENT_ID, Globals.SECRET)
        self.data = {'grant_type': 'password',
                        'username': Globals.username,
                        'password': Globals.password
                    }
        
        self.headers = {'User-Agent': 'MyBot/0.0.1'}
        self.reddit_headers = self.get_reddit_headers(self.API_BASE, self.data, self.headers)
        self.logger_name = None
        self.db_comments = set()
        self.after_dict = self.set_after_dict()
        self.total_db_reddit_entries = list()
        self.set_logger(logger_name)
        self.logger.info(Globals.global_map)
        self.collect_subreddit_id_on_initialization()
    
    def set_after_dict(self):

        # return Globals.after
        d = {}
        for e in Globals.ENDPOINTS:
            d[e] = None
        return d

    def set_logger(self, logger_name):
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)

        # sh = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s -  %(lineno)d - %(message)s")
        # sh.setFormatter(formatter)
        # self.logger.addHandler(sh)
        fh = logging.FileHandler(f'{Globals.current_dir}/logs/{logger_name}.log')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

    def collect_subreddit_id_on_initialization(self):
        query = "select id, subreddit_id, data, is_comment from subreddit_table;"
        op = db_obj.run_select_query(query)
        if op:
            for tup in op:
                id = tup[0]
                board = tup[1]
                data = tup[2]

                self.total_db_reddit_entries.append((id, board))
                self.db_comments.add(str(data))

        self.logger.info(f"Total thread Ids collected on initialization : [{len(self.total_db_reddit_entries)}]")
        

    def escape_special_characters(self, data):

        if isinstance(data, str):
            data = data.replace('#', '').replace('\\', ' ').replace('"', '').replace("'", '')
            return data

    def perform_standarization(self, json_data, is_comment=False):

        temp_created_date = json_data.get('data', {}).get('created_utc')
        dt_with_timezone = datetime.datetime.fromtimestamp(temp_created_date, timezone.utc) - timedelta(hours=5)
        created_date = dt_with_timezone.strftime('%Y-%m-%d %H:%M:%S')

        main_fields =  {
            "id":json_data["data"]["id"],
            "subreddit_id": json_data.get('data', {}).get('subreddit_id'),
            "ingestion_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "created_date":created_date
        }

        title = self.escape_special_characters(json_data.get('data', {}).get('title'))
        text =  self.escape_special_characters(json_data.get('data', {}).get('selftext'))

        self.handle_moderate_hate_speech(json_data, title, text, created_date)

        json_fields = {
            'kind': json_data.get('kind', ""),
            "subreddit": json_data.get('data', {}).get('subreddit'),
            # "text":text,
            "author_fullname": json_data.get('data', {}).get('author_fullname'),
            # "title": title,
            "subreddit_name_prefixed": json_data.get('data', {}).get('subreddit_name_prefixed'),
            "upvote_ratio": json_data.get('data', {}).get('upvote_ratio'),
            "domain": json_data.get('data', {}).get('domain'),
            "subreddit_subscribers": json_data.get('data', {}).get('subreddit_subscribers'),
            "max_comment_count": json_data.get('data', {}).get('num_comments')
        }

        return main_fields, json_fields

    def toxic_table_ingestion(self, json):
        insert_query = f"""
            INSERT INTO toxic_table (subreddit_id, author_fullname, comment, created_date, ingestion_date, is_toxic)
            VALUES ('{json["subreddit_id"]}', '{json["author_fullname"]}', '{json["comment"]}', '{json["created_date"]}', '{json["ingestion_date"]}', {json["is_toxic"]});
        """

        db_obj.run_insert_query(insert_query)
        self.logger.info(f"toxic table updated [{json["ingestion_date"]}]")

    def handle_moderate_hate_speech(self, json_data, title, text, created_date):
        if not text and not title:
            return

        if title:

            toxic_flag, ret_comment = self.hs_check_comment(title)
            
            if ret_comment:
                hatespeech_json = {
                    "subreddit_id": json_data.get('data', {}).get('subreddit_id'),
                    "author_fullname": json_data.get('data', {}).get('author_fullname'),
                    "comment": ret_comment,
                    "created_date": created_date,
                    "ingestion_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "is_toxic": toxic_flag
                }

                self.toxic_table_ingestion(hatespeech_json)
        
        if str(text) == str(title):
            return

        if text:
            toxic_flag, ret_comment = self.hs_check_comment(text)
            
            if ret_comment:
                hatespeech_json = {
                    "subreddit_id": json_data.get('data', {}).get('subreddit_id'),
                    "author_fullname": json_data.get('data', {}).get('author_fullname'),
                    "comment": ret_comment,
                    "created_date": created_date,
                    "ingestion_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "is_toxic": toxic_flag
                }

                self.toxic_table_ingestion(hatespeech_json)


    def hs_check_comment(self, comment):
        
        if not comment:
            return False, ""
        # exit()
        # print(comment)
        CONF_THRESHOLD = Globals.HATESPEECH_THREESHOLD

        data = {
            "token": Globals.HATESPEECH_TOKEN,
            "text": comment
        }

        try:
            response = requests.post(Globals.HATESPEECH_URL, json=data).json()
            # print(response)
            if response and response["class"] == "flag" and "confidence" in response and float(response["confidence"]) > CONF_THRESHOLD:
                # Do something
                return True, comment
            return False, comment
        
        except Exception as e:
            self.logger.info(f"Couldnt Fetch HATEspeech Response Error[{e}]")
            return False, ""
  
    def get_reddit_headers(self, api_base, data, headers):
        post_req = requests.post(f'{self.API_BASE}/api/v1/access_token',
                auth=self.auth, data=self.data, headers={'User-Agent': 'MyBot/0.0.1'} )
        token = post_req.json()["access_token"]
        headers = {**self.headers, **{'Authorization': f"bearer {token}"}}
        # self.logger.info(headers)
        return headers

    def fetch_comments(self, idx, params):
        url = f'{self.API_BASE}/comments/{idx}'

        req = requests.get(url, headers=self.reddit_headers, params=params)
        if req.status_code == 200:
            return req.json()[0]["data"]["children"]
        else:
            return []

    def get_subreddit_data(self):
        try:
            for endpoint in Globals.ENDPOINTS:
                if not endpoint:
                    continue

                self.logger.info(f"endp [{endpoint}]")
                for subreddit in Globals.SUBREDDIT_LIST:
                    if not subreddit:
                        continue
                    url = f"{self.API_BASE}/r/{subreddit}/{endpoint}"
                    # url = "https://oauth.reddit.com/api/v1/me"
                    # response = []
                    flag =False
                    try:
                        params = {
                            'sort': 'new',
                            'limit': 100,
                            "after": self.after_dict[endpoint],
                        }

                        req = requests.get(url, headers=self.reddit_headers, params=params)
                        if req.status_code == 200:
                            flag = True
                    except Exception as e:
                        self.logger.info(f"Going to next Subreddit [{e}]")
                        continue

                    if not flag:
                        continue

                    response = req.json()['data']['children']


                    if response:
                        self.after_dict[endpoint] = req.json()["data"]["after"]
                        self.logger.info(f"after set {self.after_dict}")

                    for each_entry in response:
                        # self.logger.info(each_entry["data"]["id"])

                        main_fields, json_fields = self.perform_standarization(each_entry)
                        id = main_fields["id"]
                        subreddit_id = main_fields["subreddit_id"]


                        comments = self.fetch_comments(id, params)  
                        time.sleep(0.7)

                        for each_comment in comments:
                            
                            main_fields, json_fields = self.perform_standarization(each_comment, is_comment=True) 

                            # if str(json_fields) in self.db_comments:
                            #     self.logger.info(f"Comment present in DB {id}")
                            #     continue

                            self.db_comments.add(str(json_fields))                                
                            insert_query = f"""
                                INSERT INTO subreddit_table (id, subreddit_id, created_date, ingestion_date, data, is_comment)
                                VALUES ('{id}', '{subreddit_id}', '{main_fields["created_date"]}', '{main_fields["ingestion_date"]}', 
                                '{json.dumps(json_fields)}', {True});
                            """
                            created_date = main_fields["created_date"]
                            db_obj.run_insert_query(insert_query)
                            self.logger.info(f"Comment inserted for subreddit [{id} {created_date}]")


                        if (id, subreddit_id) in self.total_db_reddit_entries:
                            continue
                        else:
                            insert_query = "INSERT INTO subreddit_table (id, subreddit_id, created_date, ingestion_date, data) \
                            VALUES (%s, %s, %s, %s, %s);"

                            values_to_insert = (
                                id,
                                subreddit_id,
                                main_fields["created_date"],
                                main_fields["ingestion_date"],
                                json.dumps(json_fields)
                            )

                            db_obj.run_insert_query(insert_query, values_to_insert)
                            self.total_db_reddit_entries.append((id, subreddit_id))
                            self.logger.info(f"Subreddit Data ingested {id, subreddit}")

                        
        except Exception as e:
            self.logger.info(e)
