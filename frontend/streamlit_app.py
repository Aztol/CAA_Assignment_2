import streamlit as st
import requests
import pandas as pd
import logging

logging.basicConfig(level=logging.DEBUG)

# Function to cache and fetch movie details from the backend
@st.cache_data
def autocomplete_search(search_query):
    backend_url = f'http://127.0.0.1:5000/search?q={search_query}'
    response = requests.get(backend_url)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error('Failed to fetch results from the backend.')
        return pd.DataFrame()

@st.cache_data
def fetch_movie_details(movie_id):
    movie_id = str(movie_id).strip().split()[0]
    backend_url = f'http://127.0.0.1:5000/movie-details/{movie_id}'
    response = requests.get(backend_url, params={'movie_id': movie_id})
    if response.status_code == 200:
        return response.json()
    else:
        st.error('Failed to fetch movie details.')
        return {}

@st.cache_data
def fetch_movies():
    backend_url = f'http://127.0.0.1:5000/load_all_movies'
    response = requests.get(backend_url)
    return pd.DataFrame(response.json()) if response.status_code == 200 else st.error('Failed to fetch movies from the backend.')

# Function to fetch recommendations based on liked movies
@st.cache_data
def fetch_recommendations(liked_movies):
    backend_url = f'http://127.0.0.1:5000/recommend'
    response = requests.post(backend_url, json={'liked_movies': liked_movies})
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error('Failed to fetch recommendations.')
        return pd.DataFrame()

# Main app logic
def main():
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Choose the page", ["Search and Like Movies", "View Recommendations"])
    if app_mode == "Search and Like Movies":
        search_and_like_movies()
    elif app_mode == "View Recommendations":
        view_recommendations()

def search_and_like_movies():
    st.subheader("Search and Like Movies")
    if 'liked_movies' not in st.session_state:
        st.session_state.liked_movies = []
    search_query = st.text_input('Search')
    if search_query:
        autocomplete_df = autocomplete_search(search_query)
        if not autocomplete_df.empty:
            for index, row in autocomplete_df.iterrows():
                col1, col2 = st.columns([4,1])
                with col1:
                    with st.expander(row['title']):
                        st.write(f"Genre: {', '.join(row['genres'].split('|'))}")
                        st.write(f"Movie ID: {row['movieId']}")
                with col2:
                    if st.button('Like', key=f"like_{index}"):
                        st.session_state.liked_movies.append(row['movieId'])
                        st.success(f"You liked: {row['title']}")
        else:
            st.write("No results found.")
    else:
        st.write("Please enter a search query to find movies.")
    st.write("Liked Movies:", st.session_state.liked_movies)

def view_recommendations():
    st.subheader("Your Recommendations")
    if 'liked_movies' in st.session_state and st.session_state.liked_movies:
        recommendations = fetch_recommendations(st.session_state.liked_movies)
        if not recommendations.empty:
            movie_df = fetch_movies()
            for movie in recommendations['movieId']:
                movie_details = movie_df[movie_df['movieId'] == movie]
                st.write(movie_details)
                if not movie_details.empty:
                    tmdId = movie_details['tmdbId']
                    details = fetch_movie_details(tmdId)
                    if details:
                        if details.get('poster'):  # Checks if 'poster' key exists and is not empty
                            st.image(details['poster'], width=200)
                        else:
                            st.write("No poster available")
                        st.write(f"**Plot:** {details['plot']}")
                        st.write(f"**Cast:** {', '.join(details['cast'])}")
                    st.write("---")
                else:
                    st.write(f"No movie details found for movieId: {movie}")
                if details:
                    if details.get('poster'):  # Checks if 'poster' key exists and is not empty
                        st.image(details['poster'], width=200)
                    else:
                        st.write("No poster available")
                    st.write(f"**Plot:** {details['plot']}")
                    st.write(f"**Cast:** {', '.join(details['cast'])}")
                st.write("---")
        else:
            st.write("No recommendations to show.")
    else:
        st.write("Like some movies to see recommendations!")

if __name__ == "__main__":
    main()
