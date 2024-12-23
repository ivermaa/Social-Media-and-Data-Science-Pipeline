import logging
from pyfaktory import Client, Consumer, Job, Producer
from globalparams import Globals
import time
import random
import datetime
from clients import ChanClient
from visualize import visualize
from client_reddit import RedditClient


def crawl_4chan():

    chan_client.get_catalog_threads()

    with Client(faktory_url=Globals.FAKTORY_URL, role="producer") as client:
        producer = Producer(client=client)

        run_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=Globals.SCHEDULE_TIME)
    
        run_at = run_at.isoformat()[:-7] + "Z"
        chan_client.logger.info(f"run_at = {run_at}")
        job = Job(
            jobtype="chan_job",
            args=(),
            queue="thread_queue",
            at=str(run_at),
        )
        producer.push(job)

def crawl_reddit():

    reddit_client.get_subreddit_data()

    with Client(faktory_url=Globals.FAKTORY_URL, role="producer") as client:
        producer = Producer(client=client)


        run_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=Globals.SCHEDULE_TIME)
    
        run_at = run_at.isoformat()[:-7] + "Z"
        reddit_client.logger.info(f"run_at = {run_at}")
        job = Job(
            jobtype="reddit_job",
            args=(),
            queue="reddit_queue",
            at=str(run_at),
        )
        producer.push(job)

def plot_data():

    visualize()

    with Client(faktory_url=Globals.FAKTORY_URL, role="producer") as client:
        producer = Producer(client=client)

        # figure out how to use non depcreated methods on your own
        run_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=12)
    
        run_at = run_at.isoformat()[:-7] + "Z"
        print(f"Data collection gragh plotted at = {datetime.datetime.now()}")
        job = Job(
            jobtype="plotting_job",
            args=(),
            queue="plotting_queue",
            at=str(run_at),
        )
        producer.push(job)


if __name__ == "__main__":

    print("Starting consumer")
    
    # from visualize import visualize
    plot_data()

    reddit_client = RedditClient("Reddit")
    chan_client = ChanClient("4Chan")
    
    crawl_4chan()
    crawl_reddit()
    
    with Client(faktory_url=Globals.FAKTORY_URL, role="consumer") as client:
        consumer = Consumer(client=client, queues=["thread_queue", "plotting_queue", "reddit_queue"], concurrency=3)
        # consumer.register("reddit_queue", reddit_client.get_subreddit_data())
        consumer.register("reddit_job", crawl_reddit)
        consumer.register("chan_job", crawl_4chan)
        consumer.register("plotting_job", plot_data)
        consumer.run()


    