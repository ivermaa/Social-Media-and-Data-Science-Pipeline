import psycopg2
from psycopg2 import sql
from globalparams import Globals

class DBobj():  
    def __init__(self):
        # self.conn = {
        #     'dbname': 'crawler',
        #     'user': 'postgres',
        #     'password':'postgres',
        #     'host': "127.0.0.1",
        #     'port': "5432"
        # }
        # self.conn = psycopg2.connect(**self.conn)
        # self.curr = None

        self.con = psycopg2.connect(dsn=Globals.DATABASE_URL)
        self.cur = None


    def run_select_query(self, query_str):

        try:
            self.cur = self.con.cursor()
            self.cur.execute(sql.SQL(query_str))
            op = self.cur.fetchall()
            self.cur.close()
            # print("Success.. DB connected")
            return op
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error} [{query_str}]")


    def run_insert_query(self, query_str, values=False):
        try:
            self.cur = self.con.cursor()
            if values:
                self.cur.execute(query_str, values)
            else:
                 self.cur.execute(query_str)
            self.con.commit()
            # print(f"Success.. Entry inserted [{values}]")
            self.cur.close()
            return True
            
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error: {error}")