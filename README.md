# CAA_Assignment_2

To access the streamlit app, please follow this link: https://frontend-5cmlqfzdka-oa.a.run.app

If needed, you can access directly the backend through this link: https://backend-5cmlqfzdka-oa.a.run.app
 
## Functions Description

### `get_recommendation(liked_movies, client)`
This function is designed to identify users with similar movie preferences and suggest new movies based on those similarities. The process involves:

- **Query for Similar Users**: Executes a SQL query to find the top three users (`top_3_user_id`) who have the highest number of common liked movies from a specified dataset in BigQuery. This is determined using the `liked_movies` list provided as input.
- **Fetch Predictions**: Calls `predict_recommendations`, passing the client, `liked_movies`, and the IDs of the top three similar users to fetch movie recommendations.
- **Format Recommendations**: Formats the results into a list of dictionaries, each containing the `movieId`, `title`, and `predicted_rating` of recommended movies, then returns this list.

### `predict_recommendations(client, liked_movies, top_3_user_id)`
This function generates movie recommendations using a machine learning model by:

- **Construct User ID Subquery**: Creates a subquery string from `top_3_user_id` which is used to filter user IDs in the main query.
- **Recommendation Query**: Constructs and executes a BigQuery SQL query that:
  - Uses a machine learning model to recommend movies for the users identified in the subquery.
  - Joins the results with another dataset to fetch movie titles.
  - Filters out movies that are already liked by the user.
  - Sorts the results by the predicted confidence rating of each recommended movie.
- **Collect and Return Predictions**: Collects the results into a list of dictionaries, each representing a recommended movie with its ID, title, and predicted rating, and returns this list.

Both functions utilize Google Cloud's BigQuery service for querying the database and require proper setup of query parameters and job configurations to handle the database operations effectively.
