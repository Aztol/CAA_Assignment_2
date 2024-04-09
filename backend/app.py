from flask import Flask, request, jsonify
from google.cloud import bigquery
from google.oauth2 import service_account
from elasticsearch import Elasticsearch

app = Flask(__name__)

# Load your Google Cloud credentials
credentials = service_account.Credentials.from_service_account_file(r'C:\Users\Laurent Sierro\Documents\Clef_Gcloud\bamboo-creek-415115-6445343d2370.json')

# Initialize a BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

@app.route('/')
def index():
    return "Welcome to the Movie Recommendation App Backend!"

# Placeholder route for movie search with autocomplete
@app.route('/search', methods=['GET'])
def search_movies():
    query = request.args.get('q', '')  # Get the search query from request parameters

    if query:
        # Initiate the connection to the index
        client = Elasticsearch(
            URL_ENDPOINT,
            api_key=API_KEY
        )

        # Perform search query
        response = client.search(
            index=INDEX_NAME, 
            body={
                "query": {
                    "match_phrase_prefix": {
                        "title": {
                            "query": query,
                            "max_expansions": 10  # Adjust the number of expansions as needed
                        }
                    }
                }
            }      
        )

        # Extract titles from the search results
        titles = [hit['_source']['title'] for hit in response['hits']['hits']]
        return jsonify(titles)
    
    return jsonify([])

@app.route('/recommend', methods=['GET'])
def recommend_movies():
#    user_input = request.json
    query = """
            SELECT
            userId,
            movieId,
            predicted_rating_im_confidence
            FROM
            ML.RECOMMEND(MODEL `bamboo-creek-415115.recommender.first_MF_model`,
                (SELECT 2 AS userId))
            ORDER BY
            predicted_rating_im_confidence DESC
            LIMIT 5
            """

    # Assuming 'user_input' is used to modify the query or select specific users
    
    query_job = client.query(query)  # Make an API request.
    results = query_job.result()  # Wait for the query to complete.
    
    recommendations = []
    for row in results:
        recommendations.append({
            "userId": row["userId"],
            "movieId": row["movieId"],
            "predictedRating": row["predicted_rating_im_confidence"]
        })
    
    return jsonify(recommendations)

@app.route('/posters', methods=['GET'])
def get_movie_posters():
    # Implement movie poster fetching logic here
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)
