from flask import Flask, request, jsonify
from google.cloud import bigquery
from google.oauth2 import service_account

app = Flask(__name__)

# Load your Google Cloud credentials
credentials = service_account.Credentials.from_service_account_file(r'C:\Users\Laurent Sierro\Documents\Clef_Gcloud\bamboo-creek-415115-6445343d2370.json')

# Initialize a BigQuery client
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

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

if __name__ == '__main__':
    app.run(debug=True)
