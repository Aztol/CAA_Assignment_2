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
            for movie in recommendations['movieId']:
                details = fetch_movie_details(movie)
                #st.write(details)
                if details:
                    # Adjusting the columns to give more space to text if necessary or based on content size
                    col1_width = 2
                    col2_width = 6
                    col1, col2 = st.columns([col1_width, col2_width])

                    with col1:
                        # Set a conditional width for images if needed
                        image_width = 180  # Adjusted to better fit within the column
                        if details.get('poster'):
                            st.image(details['poster'], width=image_width)
                        else:
                            st.write("No poster available")

                    with col2:
                        # Check for plot and display appropriately
                        st.write(f"**Title:** {details['title']}")
                        st.write(f"**Genres:** {', '.join(details['genres'])}")

                        if details.get('plot'):
                            st.write(f"**Plot:** {details['plot']}")
                        else:
                            st.write("No plot available")
                        
                        # Check for cast and display appropriately
                        if details.get('cast'):
                            st.write(f"**Cast:** {', '.join(details['cast'])}")
                        else:
                            st.write("No cast available")
                    
                    st.write("---")
                else:
                    pass
    else:
        st.write("Like some movies to see recommendations!")


if __name__ == "__main__":
    main()
