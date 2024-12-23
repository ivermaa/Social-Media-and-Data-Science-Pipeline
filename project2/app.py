from flask import Flask, render_template, request, jsonify
from dbconnector import DBobj

app = Flask(__name__)
db = DBobj()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sentiment')
def sentiment_page():
    return render_template('sentiment.html')

@app.route('/predictive')
def predictive_page():
    return render_template('predictive.html')

@app.route('/real-time-data', methods=['GET'])
def real_time_data():
    day = request.args.get('year')
    month = request.args.get('month')
    query = "SELECT created_date, COUNT(*) FROM toxic_table"
    filters = []
    if month:
        filters.append(f"EXTRACT(MONTH FROM created_date) = {month}")
    if day:
        filters.append(f"EXTRACT(DAY FROM created_date) = {day}")
   
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " GROUP BY created_date ORDER BY created_date"


    results = db.run_select_query(query)
    data = [{"date": str(row[0]), "count": row[1]} for row in results]

    return jsonify(data)

@app.route('/cumulative-data', methods=['GET'])
def cumulative_data():
    subreddit = request.args.get('subreddit')
    toxicity = request.args.get('toxicity')
    print(subreddit)
    print(toxicity)

    if toxicity == "yes":
        toxicity = True
    elif toxicity == "no":
        toxicity = False
    else:
        toxicity = ""

    if toxicity == "":
        if subreddit == "pol":  # Handle data for 4chan
            query = """
            SELECT 
                ingestion_date,
                COUNT(*) OVER (PARTITION BY board ORDER BY ingestion_date) AS cumulative_posts
            FROM 
                posts
            WHERE 
                board = 'pol'
            ORDER BY 
                ingestion_date ASC;
            """
        else:  # Handle data for subreddit_table
            query = f"""
            SELECT 
                ingestion_date,
                COUNT(*) OVER (PARTITION BY subreddit_id ORDER BY ingestion_date) AS cumulative_posts
            FROM 
                subreddit_table
            WHERE 
                subreddit_id = '{subreddit}'
            ORDER BY 
                ingestion_date ASC;
            """
    else:
        query =  f"""
            SELECT 
                created_date,
                COUNT(*) OVER (PARTITION BY subreddit_id ORDER BY created_date) AS cumulative_posts
            FROM 
                toxic_table
            WHERE 
                subreddit_id = '{subreddit}' and is_toxic = {toxicity}
            ORDER BY 
                created_date ASC;"""

    # print(query)
    results = db.run_select_query(query)
    data = [{"ingestion_date": str(row[0]), "cumulative_posts": row[1]} for row in results]

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)