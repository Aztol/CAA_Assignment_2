from flask import Flask, request, jsonify
from google.cloud import bigquery
from google.oauth2 import service_account
from elasticsearch import Elasticsearch
import pandas as pd
import requests
import logging

logging.basicConfig(level=logging.DEBUG)

URL_ENDPOINT =   "https://ee75f104e5a74aa484b8a41bc262cc5e.us-central1.gcp.cloud.es.io:443"
API_KEY_ELASTIC = "b0huRXhvNEI3TXF4SXc5Wl9oYmw6aFpuZkRkTDdScEtMOHA2X05jZEYtUQ=="



app = Flask(__name__)


# Load your Google Cloud credentials
#credentials = service_account.Credentials.from_service_account_file(r'C:\Users\Laurent Sierro\Documents\Clef_Gcloud\bamboo-creek-415115-6445343d2370.json')
credentials = service_account.Credentials.from_service_account_file('bamboo-creek-415115-6445343d2370.json')
# Initialize a BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

#algorithm to calculate similarity between cold start user and existing users
def get_recommendation(liked_movies, client):
    top_3_user_id = []
    similarities_query = """
    SELECT userId, COUNT(movieId) AS common_likes
    FROM `bamboo-creek-415115.recommender.ml-small-ratings`
    WHERE movieId IN UNNEST(@liked_movies)
    GROUP BY userId
    ORDER BY common_likes DESC
    LIMIT 3
    """
    query_params = [
        bigquery.ArrayQueryParameter('liked_movies', 'INT64', liked_movies),
    ]
    job_config = bigquery.QueryJobConfig(
        query_parameters=query_params
    )
    query_job = client.query(similarities_query, job_config=job_config)
    
    for row in query_job:
        top_3_user_id.append(row.userId)
    
    # Step 3: Query the recommendation model (this part is pseudo-code, adjust based on your model API)
    # Assume predict_recommendations is a function to query your recommendation model
    predictions = predict_recommendations(client, liked_movies, top_3_user_id)
    
    # Step 4: Format and return the recommendations
    recommendations = []
    for prediction in predictions:
        recommendations.append({
            "movieId": prediction["movieId"],
            "title": prediction["title"],
            "rating": prediction["predicted_rating"]
        })
    
    return recommendations

def predict_recommendations(client, liked_movies, top_3_user_id):
    # First, construct a subquery for user IDs that BigQuery can treat as a relation
    user_ids_values = ", ".join([f"({uid})" for uid in top_3_user_id])
    user_ids_subquery = f"SELECT userId FROM UNNEST([{user_ids_values}]) as userId"
    
    # Then, construct the full query using this subquery
    recommend_query = f"""
    WITH recommendations AS (
      SELECT
        recommended_movie.movieId, 
        movie.title AS title,
        predicted_rating_im_confidence AS predicted_rating
      FROM
        ML.RECOMMEND(MODEL `bamboo-creek-415115.recommender.first_MF_model`,(
                    SELECT userId, movieId,
                    FROM bamboo-creek-415115.recommender.ratings                   
                    WHERE userId IN UNNEST([{user_ids_values}]))) AS recommended_movie
      JOIN
        `bamboo-creek-415115.recommender.ml-small-movies` AS movie
      ON
        recommended_movie.movieId = movie.movieId
      WHERE
        recommended_movie.movieId NOT IN UNNEST(@liked_movies)
      ORDER BY
        predicted_rating DESC
      LIMIT 10
    )
    SELECT * FROM recommendations
    """
    print(recommend_query)
    query_params = [
        bigquery.ArrayQueryParameter("liked_movies", "INT64", liked_movies),
    ]
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    query_job = client.query(recommend_query, job_config=job_config)

    predictions = []
    for row in query_job:
        predictions.append({
            "movieId": row.movieId,
            "title": row.title,
            "predicted_rating": row.predicted_rating
        })

    return predictions

def fetch_movie_details(movie_id, api_key):
 
    query = """
    SELECT links.tmdbId, movies.title, movies.genres
    FROM `bamboo-creek-415115.recommender.ml-small-links` links
    JOIN `bamboo-creek-415115.recommender.ml-small-movies` movies
    ON links.movieId = movies.movieId
    WHERE links.movieId = @movie_id
    """
    query_params = [
        bigquery.ScalarQueryParameter("movie_id", "INT64", movie_id),
    ]
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    query_job = client.query(query, job_config=job_config)

    # Execute the query and get the result
    result = query_job.result()

    # Fetch the first row
    row = list(result)[0]
    tmdb_id = row.tmdbId
    title = row.title
    genres = row.genres.split('|')  # Assuming genres are stored as a pipe-separated string

    base_url = "https://api.themoviedb.org/3"
    movie_url = f"{base_url}/movie/{tmdb_id}?api_key={api_key}"
    credits_url = f"{base_url}/movie/{tmdb_id}/credits?api_key={api_key}"

    # Fetch movie details from TMDB API
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
        'title': title,
        'genres': genres,
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
    api_key = "b0864169651f3978f7da5639f393979c"
    details = fetch_movie_details(movie_id, api_key)
    return jsonify(details)

@app.route('/search', methods=['GET'])
def search_movies():
    query = request.args.get('q', '')  # Get the search query from request parameters

    if query:
        client = Elasticsearch(URL_ENDPOINT, api_key=API_KEY_ELASTIC)
        response = client.search(
            index='caa-assignment-movies', 
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
        print(results)
        return jsonify(results)
    
    return jsonify([])

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.get_json()
    liked_movies = data.get('liked_movies', [])
    if not liked_movies:
        return jsonify({"error": "liked_movies is required"}), 400
    return get_recommendation(liked_movies, client)

if __name__ == '__main__':
    app.run(debug=True)




if __name__ == '__main__':
    app.run(debug=True)
