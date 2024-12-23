import requests
import json
from dbconnector import DBobj
from globalparams import Globals
# from pyfaktory import Job
import datetime
import psycopg2
from psycopg2 import sql
import time
import logging
from collections import deque


db_obj = DBobj()


class ChanClient():
    def __init__(self, logger_name):
        self.API_BASE =  Globals.CHAN_4BASE
        self.boards = Globals.BOARDS
        self.logger = None
        self.set_logger(logger_name)
        self.total_db_thread_ids = list()
        self.total_db_posts_count = set()
        self.thread_set = set() 
        self.collect_thread_id_on_initialization()
        self.last_ingestion_date = None
        self.last_modification_date = None
        self.logger.info(f"global map: {Globals.global_map}")
    
    def set_logger(self, logger_name):
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        # sh = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        # sh.setFormatter(formatter)
        # self.logger.addHandler(sh)
        fh = logging.FileHandler(f'{Globals.current_dir}/logs/{logger_name}.log')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)


    def collect_thread_id_on_initialization(self):
        query = "select id, board from thread_table;"
        op = db_obj.run_select_query(query)
        if op:
            for tup in op:
                id = int(tup[0])
                board = tup[1]
                self.total_db_thread_ids.append((id, board))
                self.thread_set.add(id)

        self.logger.info(f"Total thread Ids collected on initialization : [{len(self.total_db_thread_ids)}]")
        

        query = "select count(*) from posts;"
        op = db_obj.run_select_query(query)
        self.total_db_posts_count = int(op[0][0])
        self.logger.info(f"Total posts in db: [{self.total_db_posts_count}]")


    def populate_last_ingested_details(self):
        query = "select ingestion_date, last_modified from thread_table order by last_modified desc limit 1;"
        op = db_obj.run_select_query(query)
        if op:
            self.ingestion_date = op[0]
            self.last_modification_date = op[1] 
        
        self.logger.info(f"Total thread Ids collected on initialization : Ingestion Date: [{self.last_ingestion_date}], Modified Date: [{self.last_modification_date}]]")

        if not self.last_ingestion_date or not self.last_modification_date:
            exit("modification Date or ingestion date empty")

    def get_catalog_threads(self):
        try:
            for board in self.boards:
                if not board:
                    continue
                request_pieces = [board, "catalog.json"]
                api_call = self.build_request(request_pieces)
                ret_json = self.execute_request(api_call)
                standard_catalog = self.perform_standarization(ret_json, board)
                
                local_set = set()
                for main_fields, json_fields in standard_catalog:
                    thread_id = main_fields["id"]
                    if (thread_id, board) in self.total_db_thread_ids:
                        continue
                    else:
                        
                        insert_query = "INSERT INTO thread_table (id, board, last_modified, ingestion_date, data) \
                        VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id, board) DO NOTHING;"

                        values_to_insert = (
                            thread_id,
                            main_fields["board"],
                            main_fields["last_modified"],
                            main_fields["ingestion_date"],
                            json.dumps(json_fields)
                        )

                        db_obj.run_insert_query(insert_query, values_to_insert)
                        self.total_db_thread_ids.append((thread_id, board))
                        local_set.add(thread_id)
                        self.logger.info(f"({thread_id}, {board}) iserted DB..")


                if not local_set:
                    continue
                
                self.logger.info(f"Total new posts for board [{board}] to be ingested: [{len(local_set)}]")

                for thread_num in local_set:
                    request_pieces = [board, "thread", f"{thread_num}.json"]
                    api_call = self.build_request(request_pieces)
                    ret_json = self.execute_request(api_call)

                    for post in ret_json["posts"]:
                        post_number = post["no"]
                        post_ingestion_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        insert_query = "INSERT INTO posts (board, thread_number, post_number, ingestion_date, data) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (board, thread_number, post_number)  DO NOTHING;"
                        
                        values_to_insert = (
                            board,
                            thread_num,
                            post_number,
                            post_ingestion_date,
                            json.dumps(post)
                        )
                        db_obj.run_insert_query(insert_query, values_to_insert)
                        self.total_db_posts_count += 1

                local_set = {}
                    
            query = "select count(*) from thread_table;"
            op = db_obj.run_select_query(query)
            self.logger.info(f"4chan Data collected: {op[0]} =  {len(self.total_db_thread_ids)}")

            query = "select count(*) from posts;"
            op = db_obj.run_select_query(query)
            self.logger.info(f"4chan posts collected: {op[0]} {self.total_db_posts_count}")
        except Exception as e:
            self.logger.info(e)

    def perform_standarization(self, json_list, board):
        ret = []
        for page in json_list:
            for thread in page['threads']:
                # for thread_json in thread_list:
                main_fields = {
                    "id" : thread.get("no"),
                    "board": board, 
                    "last_modified" : datetime.datetime.fromtimestamp(thread.get("last_modified"), tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                    "ingestion_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                json_fields = thread

                ret.append((main_fields,json_fields))

        return ret

    def build_request(self, request_pieces):
        api_call = "/".join([self.API_BASE] + request_pieces)
        return api_call

    def execute_request(self, api_call):
        resp = requests.get(api_call)  # error handling neede
        json = resp.json()  # error handling neede
        # self.logger.info(json)
        return json






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
        self.total_db_reddit_entries = list()
        self.set_logger(logger_name)
        self.logger.info(Globals.global_map)
        self.collect_subreddit_id_on_initialization()


    def set_logger(self, logger_name):
        self.logger = logging.getLogger(logger_name)
        self.logger.propagate = False
        self.logger.setLevel(logging.INFO)
        # sh = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        # sh.setFormatter(formatter)
        # self.logger.addHandler(sh)
        fh = logging.FileHandler(f'{Globals.current_dir}/logs/{logger_name}.log')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)


    def collect_subreddit_id_on_initialization(self):
        query = "select id, subreddit_id from subreddit_table;"
        op = db_obj.run_select_query(query)
        if op:
            for tup in op:
                id = tup[0]
                board = tup[1]
                self.total_db_reddit_entries.append((id, board))

        self.logger.info(f"Total thread Ids collected on initialization : [{len(self.total_db_reddit_entries)}]")
        

        query = "select count(*) from posts;"
        op = db_obj.run_select_query(query)
        self.total_db_posts_count = int(op[0][0])
        self.logger.info(f"Total posts in db: [{self.total_db_posts_count}]")

    def perform_standarization(self, json_data):
        main_fields =  {
                "id":json_data["data"]["id"],
                "subreddit_id": json_data.get('data', {}).get('subreddit_id'),
                "ingestion_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "created_date":datetime.datetime.utcfromtimestamp(json_data.get('data', {}).get('created_utc')).strftime('%Y-%m-%d %H:%M:%S')
            }
        
        json_fields = {
            'kind': json_data.get('kind', ""),
            "subreddit": json_data.get('data', {}).get('subreddit'),
            # "text": json_data.get('data', {}).get('selftext'),
            "author_fullname": json_data.get('data', {}).get('author_fullname'),
            # "title": json_data.get('data', {}).get('title'),
            "subreddit_name_prefixed": json_data.get('data', {}).get('subreddit_name_prefixed'),
            "upvote_ratio": json_data.get('data', {}).get('upvote_ratio'),
            "domain": json_data.get('data', {}).get('domain'),
            "subreddit_subscribers": json_data.get('data', {}).get('subreddit_subscribers'),
            "max_comment_count": json_data.get('data', {}).get('num_comments')
        }

        return main_fields, json_fields

    def get_reddit_headers(self, api_base, data, headers):
        post_req = requests.post(f'{self.API_BASE}/api/v1/access_token',
                auth=self.auth, data=self.data, headers={'User-Agent': 'MyBot/0.0.1'} )
        token = post_req.json()["access_token"]
        headers = {**self.headers, **{'Authorization': f"bearer {token}"}}
        # self.logger.info(headers)
        return headers

    def get_subreddit_data(self):
        try:
            for endpoint in Globals.ENDPOINTS:
                for subreddit in Globals.SUBREDDIT_LIST:
                    if not subreddit:
                        continue
                    url = f"{self.API_BASE}/r/{subreddit}/{endpoint}"
                    # url = "https://oauth.reddit.com/api/v1/me"
                    try:
                        req = requests.request("GET", url, headers=self.reddit_headers).json()
                    except Exception as e:
                        self.logger.info(f"Going to next Subreddit [{e}]")
                        continue

                    response = req['data']['children']
                    # data_list = []

                    for each_entry in response:
                        # self.logger.info(each_entry["data"]["id"])

                        main_fields, json_fields = self.perform_standarization(each_entry)
                        id = main_fields["id"]
                        subreddit_id = main_fields["subreddit_id"]

                        if (id, subreddit_id) in self.total_db_reddit_entries:
                            continue
                        else:
                            insert_query = "INSERT INTO subreddit_table (id, subreddit_id, created_date, ingestion_date, data) \
                            VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id, subreddit_id) DO NOTHING;"

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

                q = "select count(*) from subreddit_table;"
                op = db_obj.run_select_query(q)
                self.logger.info(f"Reddit Data collected: {op[0]} = {len(self.total_db_reddit_entries)}")

        except Exception as e:
            self.logger.info(e)



# if __name__== "__main__":
#     # db_obj = DBobj()
#     reddit_obj = RedditClient("Reddit")
#     chan_client = ChanClient("4Chan")

#     while True:
#         reddit_obj.get_subreddit_data()
#         chan_client.get_catalog_threads()
#         time.sleep(10)





