# CAA_Assignment_2
Goal: You will create a movie recommendation application. You will implement a simple interface that accepts a user’s movie preferences and shows the user movie recommendations based on their preference. The application should run on the Google cloud.

Fonction recommendation logic.
1/ the function get a list containing movieId of liked movies from the user. it is called liked_movies
2/ Bigquery to find top 3 most similar user only from bamboo-creek-415115.recommender.ml-small-ratings using the liked_movies parameter
3/ Store the userId of those 3 user in a list called top_3_user_id
3/ Query to the recommend model to make prediction for those 3 users with highest predicted_rating_confidence with params : liked_movies and top_3_user_id
4/ return jsonised containing movieId, title et rating

Here is some context.
I make a backend flask app to call a recommendation matrix factorisation model on google cloud. I want you to code the recommendation fonction called get_reccommendation(). The different dataset are the followed :
- bamboo-creek-415115.recommender.ml-small-movies containing movieId INTEGER NULLABLE title STRING	NULLABLE genres STRING	NULLABLE
- bamboo-creek-415115.recommender.ml-small-ratings contaigning userId INTEGER NULLABLE movieId INTEGER NULLABLE date TIMESTAMP NULLABLE rating_im FLOAT NULLABLE	
Fonction recommendation logic.
1/ the function get a list containing movieId of liked movies from the user. it is called liked_movies
2/ Bigquery to find top 3 most similar user only from bamboo-creek-415115.recommender.ml-small-ratings using the liked_movies parameter
3/ Store the userId of those 3 user in a list called top_3_user_id
3/ Query to the recommend model to make prediction for those 3 users with highest predicted_rating_confidence with params : liked_movies and top_3_user_id
4/ return jsonised containing movieId, title et rating
