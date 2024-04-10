from flask import Flask, request, jsonify
from google.cloud import bigquery
from google.oauth2 import service_account
from elasticsearch import Elasticsearch
import pandas as pd
import requests
import logging

logging.basicConfig(level=logging.DEBUG)

URL_ENDPOINT =   "https://ee75f104e5a74aa484b8a41bc262cc5e.us-central1.gcp.cloud.es.io:443"
API_KEY = "b0huRXhvNEI3TXF4SXc5Wl9oYmw6aFpuZkRkTDdScEtMOHA2X05jZEYtUQ=="
INDEX_NAME = 'caa-assignment-movies'


app = Flask(__name__)

# Load your Google Cloud credentials
credentials = service_account.Credentials.from_service_account_file(r'C:\Users\Laurent Sierro\Documents\Clef_Gcloud\bamboo-creek-415115-6445343d2370.json')

# Initialize a BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

#algorithm to calculate similarity between cold start user and existing users
def calculate_similarity(user_movie_preferences, recommendations_df):

    def calculate_similarity_and_weighted_scores(row):

        shared_movies = set(row['top_5_prediction']).intersection(user_movie_preferences)
        similarity_number = len(shared_movies)
        score_weighted = sum([(5 - row['top_5_prediction'].index(movie)) for movie in shared_movies])
        
        return pd.Series([similarity_number, score_weighted], index=['similarity_number', 'score_weighted'])

    recommendations_df[['similarity_number', 'score_weighted']] = recommendations_df.apply(calculate_similarity_and_weighted_scores, axis=1)
    
    ordered_recommendations = recommendations_df.sort_values(by=['similarity_number', 'score_weighted'], ascending=[False, False])



    def generate_recommendations(ordered_recommendations, recommendations_df, user_movie_preferences, user_id):
        # Filter similarity scores for the cold user
        cold_user_similarity_scores = ordered_recommendations[ordered_recommendations['userId'] != user_id].head(3)

        # Get the top recommended movies for the cold user
        top_recommendations = cold_user_similarity_scores.head(1)['top_5_prediction'].values[0]

        # Remove movies that the cold user has already liked
        new_recommendations = [movie for movie in top_recommendations if movie not in user_movie_preferences]

        # Create a DataFrame of new movie recommendations
        recommendations_df = pd.DataFrame({'movieId': new_recommendations})

        return recommendations_df
    
    generated_recommendations = generate_recommendations(ordered_recommendations, recommendations_df, user_movie_preferences, 612)

    return generated_recommendations

def fetch_movie_details(movie_id, api_key):
    base_url = "https://api.themoviedb.org/3"
    movie_url = f"{base_url}/movie/{movie_id}?api_key={api_key}"
    credits_url = f"{base_url}/movie/{movie_id}/credits?api_key={api_key}"

    # Fetch movie details
    movie_response = requests.get(movie_url)
    movie_details = movie_response.json() if movie_response.status_code == 200 else {}

    # Fetch movie credits/cast
    credits_response = requests.get(credits_url)
    credits_details = credits_response.json() if credits_response.status_code == 200 else {}

    # Extract required details
    poster_path = movie_details.get('poster_path', '')
    plot = movie_details.get('overview', 'Plot details not available.')
    cast = [person['name'] for person in credits_details.get('cast', [])][:5]  # Get top 5 cast members

    # Construct full poster URL
    poster_full_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ''

    return {
        'poster': poster_full_url,
        'plot': plot,
        'cast': cast
    }

@app.route('/load_all_movies', methods=['GET'])
def load_movies():
    query = """
    SELECT m.*, l.imdbId, l.tmdbId FROM `bamboo-creek-415115.recommender.ml-small-movies` m
    INNER JOIN `bamboo-creek-415115.recommender.ml-small-links` l ON m.movieId = l.movieId;
    """
    
    # Execute the query and convert results to DataFrame
    query_job = client.query(query)
    movies_df = query_job.to_dataframe()

    return movies_df.to_json()

@app.route('/')
def index():
    return "Welcome to the Movie Recommendation App Backend!"

@app.route('/movie-details/<int:movie_id>', methods=['GET'])
def movie_details(movie_id):
    api_key = "a4e9b16805164cf6c06689a7bb8da071"
    details = fetch_movie_details(movie_id, api_key)
    return jsonify(details)

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
        results = [{
            "title": hit['_source']['title'],
            "genres": hit['_source'].get('genres', 'Unknown'),  # Use .get() to handle missing fields
            "movieId": hit['_source']['movieId']
        } for hit in response['hits']['hits']]

        return jsonify(results)
    
    return jsonify([])

@app.route('/recommend', methods=['POST'])
def recommend_movies():
    data = request.get_json()
    cold_user_movies = data.get('liked_movies', "No data received")

    if cold_user_movies == "No data received":
        return "No data received", 400
    recommendation_query = """
    SELECT * FROM
    ML.RECOMMEND(MODEL `bamboo-creek-415115.recommender.first_MF_model`,
    (
    SELECT DISTINCT userId
    FROM `bamboo-creek-415115.recommender.ml-small-ratings`
    LIMIT 5))
    """

    # Run the recommendation query
    recommendation_result = client.query(recommendation_query).to_dataframe()

    # Group by 'userId' and then apply the nlargest method to get the top 5 for each group
    top_5_per_user = recommendation_result.groupby('userId', group_keys=False).apply(lambda x: x.nlargest(5, 'predicted_rating_im_confidence'))


    # Group by 'userId' and aggregate 'movieId' into a list for each user
    top_5_movies_per_user = top_5_per_user.groupby('userId')['movieId'].apply(list).reset_index(name='top_5_prediction')

    # Call the function
    new_recommendations = calculate_similarity(cold_user_movies, top_5_movies_per_user)


    
    return jsonify(new_recommendations.to_dict(orient='records'))




if __name__ == '__main__':
    app.run(debug=True)
