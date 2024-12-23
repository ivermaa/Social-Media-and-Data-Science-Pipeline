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


class ChanClient():
    def __init__(self, logger_name):
        self.API_BASE =  Globals.CHAN_4BASE
        self.boards = Globals.BOARDS
        self.logger = None
        self.set_logger(logger_name)
        self.total_db_thread_ids = list()
        self.total_db_posts_count = set()
        self.db_posts = set()
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
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s -  %(lineno)d - %(message)s")
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
                self.thread_set.add(str(id))

        self.logger.info(f"Total thread Ids collected on initialization : [{len(self.total_db_thread_ids)}]")
        print(len(self.thread_set))

        query = "select board, thread_number, post_number from posts;"
        op = db_obj.run_select_query(query)
        if op:
            for tup in op:
                board = tup[0]
                thread_num = tup[1]
                post_number = tup[2]
                
                self.db_posts.add((board, int(thread_num), int(post_number)))



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
                time.sleep(0.1)
                local_set = set()
                for main_fields, json_fields in standard_catalog:
                    
                    thread_id = main_fields["id"]

                    self.thread_set.add(thread_id)
                    thread_num =  thread_id


                    request_pieces = [board, "thread", f"{thread_num}.json"]
                    time.sleep(0.3)

                    api_call = self.build_request(request_pieces)
                    ret_json = self.execute_request(api_call)
                    
                    for post in ret_json["posts"]:
                        post_number = post["no"]
                        post_ingestion_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                        if (board, thread_num, post_number) in self.db_posts:
                            continue
                        
                        self.db_posts.add((board, int(thread_num), int(post_number)))

                        self.perform_toxic_posts(post, main_fields["last_modified"], board)

                        insert_query = "INSERT INTO posts (board, thread_number, post_number, ingestion_date, data) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (board, thread_number, post_number)  DO NOTHING;"
                        
                        values_to_insert = (
                            board,
                            thread_num,
                            post_number,
                            post_ingestion_date,
                            json.dumps(post)
                        )
                        
                        ret = db_obj.run_insert_query(insert_query, values_to_insert)

                        self.logger.info(f"inserted {post_number}")


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
                        self.total_db_thread_ids.append((int(thread_id), board))
                        local_set.add(thread_id)
                        self.logger.info(f"({thread_id}, {board}) inserted DB..")

        except Exception as e:
            self.logger.info(e)

    def escape_special_characters(self, data):
        if isinstance(data, str):
            data = data.replace('#', '') \
                .replace('\\', ' ') \
                .replace('"', '') \
                .replace("'", '') \
                .replace('<', ' ') \
                .replace('&', ' ') \
                .replace('>', ' ') \
                .replace('/', ' ') \
                .replace('=', ' ')
            return data
    
    def perform_toxic_posts(self, data, created_date, board):

        ret_comment = data["com"]
        ret_comment = self.escape_special_characters(ret_comment)
        
        if ret_comment:
            self.handle_moderate_hate_speech(ret_comment, created_date, board)
        else:
            print(f"ret_comment : {ret_comment}")

    def handle_moderate_hate_speech(self, comment, created_date, board):
        
        toxic_flag, ret_comment = self.hs_check_comment(comment)

        if ret_comment:
            hatespeech_json = {
                "subreddit_id": board,
                "author_fullname": "user_4chan",
                "comment": ret_comment,
                "created_date": created_date,
                "ingestion_date": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "is_toxic": toxic_flag
            }
            self.toxic_table_ingestion(hatespeech_json)

    def toxic_table_ingestion(self, json):
        insert_query = f"""
            INSERT INTO toxic_table (subreddit_id, author_fullname, comment, created_date, ingestion_date, is_toxic)
            VALUES ('{json["subreddit_id"]}', '{json["author_fullname"]}', '{json["comment"]}', '{json["created_date"]}', '{json["ingestion_date"]}', {json["is_toxic"]});
        """

        db_obj.run_insert_query(insert_query)
        self.logger.info(f"toxic table updated [{json["ingestion_date"]}]")
    

    def hs_check_comment(self, comment):
        
        if not comment:
            return False, ""
        # exit()
        print(comment)
        CONF_THRESHOLD = Globals.HATESPEECH_THREESHOLD

        data = {
            "token": Globals.HATESPEECH_TOKEN,
            "text": comment
        }

        try:
            response = requests.post(Globals.HATESPEECH_URL, json=data).json()
            print(f"4chan {response}" )
            # print(response)
            if response and response["class"] == "flag" and "confidence" in response and float(response["confidence"]) > CONF_THRESHOLD:
                # Do something
                return True, comment    
            return False, comment
        except Exception as e:
            self.logger.info(f"Couldnt Fetch HATESpeech Response Error [{e}]")
            return False, ""


    def perform_standarization(self, json_list, board):
        ret = []
        for page in json_list:
            for thread in page['threads']:
                # for thread_json in thread_list:
                temp_created_date = thread.get('last_modified')
                dt_with_timezone = datetime.datetime.fromtimestamp(temp_created_date, timezone.utc) - timedelta(hours=5)
                created_date = dt_with_timezone.strftime('%Y-%m-%d %H:%M:%S')

                main_fields = {
                    "id" : thread.get("no"),
                    "board": board, 
                    "last_modified" : created_date,
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

# if __name__== "__main__":
#     # db_obj = DBobj()
#     reddit_obj = RedditClient("Reddit")
#     chan_client = ChanClient("4Chan")

#     while True:
#         reddit_obj.get_subreddit_data()
#         chan_client.get_catalog_threads()
#         time.sleep(10)





