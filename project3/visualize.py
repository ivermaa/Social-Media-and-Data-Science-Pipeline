import matplotlib.pyplot as plt
from globalparams import Globals
from dbconnector import DBobj


def visualize():
    
    obj = DBobj()

    for table in ["posts", "subreddit_table", "thread_table"]:
        query = f'''SELECT ingestion_date, SUM(COUNT(*)) OVER (ORDER BY ingestion_date) AS cumulative_sum FROM {table}
        GROUP BY 
            ingestion_date
        ORDER BY 
            ingestion_date;'''
    
        query = f'''SELECT  date_trunc('hour', ingestion_date) + (extract(hour FROM ingestion_date)::integer / 6) * interval '6 hours' AS ingestion_date,
        SUM(COUNT(*)) OVER (ORDER BY date_trunc('hour', ingestion_date) + (extract(hour FROM ingestion_date)::integer / 6) * interval '6 hours') AS cumulative_sum FROM {table} 
        GROUP BY 
            ingestion_date
        ORDER BY 
            ingestion_date;'''

        query2 = f"""SELECT 
            EXTRACT(DAY FROM ingestion_date) AS day, 
            COUNT(*) AS post_count,
            SUM(COUNT(*)) OVER (ORDER BY EXTRACT(DAY FROM ingestion_date)) AS cumulative_sum
        FROM 
            posts
        WHERE 
            board = 'sci'
        GROUP BY 
            EXTRACT(DAY FROM ingestion_date)
        ORDER BY 
            day;
        """

        op  = obj.run_select_query(query)

        if op: 
            # Process results for plotting
            ingestion_dates = [row[0] for row in op]  # Adjust date format as necessary
            cumulative_sums = [row[1] for row in op]

            plt.figure(figsize=(10, 6))
            plt.plot(ingestion_dates, cumulative_sums, label=f'Data Collection Window [{table}]', marker='o')
            plt.xlabel('Ingestion Date')
            plt.ylabel('Count in DB')
            plt.title('Cumulative Sum')
            plt.legend()
            plt.grid(True)

            plt.savefig(f'{Globals.current_dir}/{table}_plot.png')