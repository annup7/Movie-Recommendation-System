import streamlit as st
import pickle
import pandas as pd
import requests
import base64
import psycopg2
import os

DATABASE_URL = "postgresql://neondb_owner:gF0iuBzlO5Yk@ep-morning-river-a19sgi22.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

def connect_to_db():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        st.success("Connected to the database successfully!")
        return conn
    except Exception as e:
        st.error(f"Error connecting to the database: {e}")
        return None


def insert_movie_recommendations(conn, recommendations):
    """Insert movie recommendations into the database table."""
    if conn is None:
        st.error("Database connection is not established.")
        return

    try:
        with conn.cursor() as cur:
            insert_query = """
                INSERT INTO movie_recommendations (movie_name, poster_url, overview, genres, imdb_rating, trailer_url, "cast")
                VALUES (%s, %s, %s, %s, %s, %s, %s) 
                RETURNING id;
            """
            for movie, poster, overview, genres, imdb_rating, trailer_url, cast in recommendations:
                st.write(f"Processing movie: {movie}")
                if not all([movie, poster, overview, genres, imdb_rating, trailer_url, cast]):
                    st.error(f"Incomplete data for {movie}. Skipping.")
                    continue
                st.write(f"Inserting data: (movie_name={movie}, poster_url={poster}, overview={overview}, genres={genres}, imdb_rating={imdb_rating}, trailer_url={trailer_url}, cast={cast})")
                try:
                    cur.execute(insert_query, (movie, poster, overview, genres, imdb_rating, trailer_url, cast))
                    conn.commit()
                    st.success(f"Inserted {movie} into the database successfully!")
                except Exception as e:
                    st.error(f"Error during insert for {movie}: {e}")
                    st.write(f"Details: {e}")
                    conn.rollback()

    except psycopg2.Error as e:
        conn.rollback()
        st.error(f"Error inserting data: {e.pgcode} - {e.pgerror}")
        st.write(f"Details: {e}")

    except Exception as e:
        conn.rollback()
        st.error(f"Error inserting data: {e}")
        st.write(f"Details: {e}")


# Encode the local image to base64
def get_base64_image(file_path):
    with open(file_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Convert the local image
background_image = get_base64_image("static/images/img.png")


def fetch_movie_details(movie_title):
    """Fetch movie details, including poster URL, overview, genres, IMDB rating, and where to watch."""
    omdb_api_key = '683574bd'  # Replace with your OMDB API key
    youtube_api_key = 'AIzaSyBf6xa3wVlac00dTvb9TRgK692EiLnWiZo'  # Replace with your YouTube API key
    omdb_url = f"https://www.omdbapi.com/?apikey={omdb_api_key}&t={movie_title}"
    
    try:
        response = requests.get(omdb_url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            if data.get('Response') == "True":
                poster_url = data.get('Poster', None)
                overview = data.get('Plot', "Overview not available.")
                genres = data.get('Genre', "N/A")
                imdb_rating = data.get('imdbRating', "N/A")
                trailer_url = None
                cast = data.get('Actors', "Cast not available.")

                # Fetch trailer from YouTube
                if 'Title' in data:
                    search_query = f"{data['Title']} trailer"
                    youtube_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={search_query}&key={youtube_api_key}"
                    youtube_response = requests.get(youtube_url).json()

                    # Check if YouTube returned any results
                    if youtube_response.get('items'):
                        first_item = youtube_response['items'][0]
                        video_id = first_item.get('id', {}).get('videoId', None)
                        if video_id:
                            trailer_url = f"https://www.youtube.com/watch?v={video_id}"

                return poster_url, overview, genres, imdb_rating, trailer_url, cast
        return None, "Overview not available.", "N/A", "N/A", None, "Cast not available."
    except requests.exceptions.Timeout:
        st.error("The request to fetch movie details timed out. Please try again later.")
        return None, "Overview not available due to timeout.", "N/A", "N/A", None, "Cast not available."
    except requests.exceptions.RequestException as e:
        # Handle quota limit or other request errors gracefully
        st.error(f"An error occurred: {e}")
        if "quota" in str(e).lower():
            st.warning("YouTube API quota reached. Skipping trailer URL.")
        return None, "Overview not available due to an error.", "N/A", "N/A", None, "Cast not available."

def fetch_imdb_rating(imdb_id):
    """
    Fetch IMDB rating using OMDB API.
    """
    omdb_api_key = "683574bd"  # Replace with your OMDB API key
    omdb_url = f"https://www.omdbapi.com/?apikey={omdb_api_key}&i={imdb_id}"
    try:
        response = requests.get(omdb_url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return data.get("imdbRating", "N/A")
    except requests.exceptions.RequestException:
        return "N/A"
    return "N/A"

def recommend(movie):
    try:
        index = movies[movies['title'] == movie].index[0]
        distances, indices = nn.kneighbors(tfidf_matrix[index], n_neighbors=6)
        recommend_movies = movies['title'].iloc[indices.flatten()[1:]].tolist()

        recommend_movies_with_details = []
        for recommended_movie in recommend_movies:
            poster_url, overview, genres, imdb_rating, trailer_url, cast = fetch_movie_details(recommended_movie)
            recommend_movies_with_details.append((recommended_movie, poster_url, overview, genres, imdb_rating, trailer_url, cast))

        return recommend_movies_with_details
    except IndexError:
        return [("Error: Movie not found in the dataset", None, "Overview not available.", "N/A", "N/A", None, "Cast not available.")]




# Load pickled files
nn = pickle.load(open('nn.pkl', 'rb'))
tfidf_matrix = pickle.load(open('tfidf.pkl', 'rb'))
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)

# Full-width navbar CSS
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap');
            
     /* Apply Poppins font to all elements */
    body, .css-1d391kg, .css-1aumxhk, .css-1daw9f6, .css-1ysk81j, .stApp, [class*="st"] {{
        font-family: 'Poppins', sans-serif !important;
    }}

    /* Additional customization for Streamlit text elements */
    .stText, .stMarkdown, .stSubheader, .stHeader, .stTextInput, .stSelectbox, .stButton {{
        font-family: 'Poppins', sans-serif !important;
    }}
            
    .navbar {{
        width: 100%;
        background-color: rgba(0, 0, 0, 0.8);
        padding: 1px 25px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1000;
    }}
    .navbar img {{
        height: 35px;
        margin-top: 68px;
        width: 40px;
        object-fit: cover;  /* Adjust to move the image down */
        border-radius: 50%;
    }}
    .navbar .title {{
        font-size: 1.8em;
        font-weight: bold;
        color: white;
        margin-left: 8px;
        margin-top: 70px;  /* Adjust to move the title down */
    }}
    
    .main {{
        margin-top: 30px; /* Adjust for navbar height */
        padding: 10px;  /* Adds some space around content */
    }}

    .custom-title {{
        font-size: 3em;  /* Make the title bigger */
        font-weight: 500;  /* Make the title bold */
        text-align: center;  /* Center align the title */
        color: #E50914;  /* Change to your preferred color */
    }}   
    
    html, body {{
        height: 100%;
        margin: 0;
        background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url("data:image/png;base64,{background_image}");
        background-size: 380px 380px;  /* Ensures the image covers the entire screen */
        background-attachment: fixed;  /* Makes the background stay fixed during scrolling */
        background-position: 0 0;  /* Centers the background image */
        background-repeat: repeat;  /* Prevents the image from repeating */
        animation: animatedBackground 900s linear infinite;
    }}
    .stApp {{
        background-color: transparent;  /* Makes the app content background transparent */
         max-width: 100% !important;
    padding: 10px;
    }}

     div.stButton > button {{
        background-color: #E50914; /* Netflix red */
        color: white; /* White font */
        border: none; /* No border */
        padding: 10px 20px; /* Padding for size */
        font-size: 16px; /* Font size */
        font-weight: bold; /* Bold font */
        border-radius: 5px; /* Rounded corners */
        cursor: pointer; /* Pointer cursor on hover */
        transition: all 0.3s ease-in-out; /* Smooth transition for hover */
    }}

    /* Hover styling */
    div.stButton > button:hover {{
        background-color: #B00710; /* Darker Netflix red */
        color: white; /* White font */
        transform: translateY(-3px); /* Move up slightly */
        box-shadow: 0 5px 15px rgba(229, 9, 20, 0.4); /* Add a glowing shadow */
    }}

    img {{
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    img:hover {{
        transform: scale(1.05);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }}
            
    @keyframes animatedBackground {{
        0% {{
            background-position: 0 0;
        }}
        100% {{
            background-position: 7000px 000px;  /* Adjust for desired animation direction and speed */
        }}
    }}

    .footer {{
        width: 100%;
        background-color: rgba(0, 0, 0, 0.8); /* Matches navbar color */
        color: white; /* Text color */
        text-align: center; /* Center-align text */
        padding: 0 0; /* Padding for spacing */
        position: fixed;
        bottom: 0;
        left: 0;
        z-index: 1000;
        font-size: 13px; /* Font size */
    }}
    .footer a {{
        color: #E50914; /* Netflix red for links */
        text-decoration: none; /* No underline */
        font-weight: bold; /* Bold links */
        font-size: 14px;
        margin-right: 1px;
    }}
    .footer a:hover {{
        text-decoration: underline; /* Underline on hover */
        color: #B00710; /* Darker Netflix red */
        font-size: 14px;
    }}
    .netflix-red {{
    color: #E50914; /* Netflix red */
    font-weight: bold;
    }}

    @media (max-width: 576px) {{
        .main{{
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            text-align: center;
            margin-top: 0; /* Adjust for navbar height */
            padding: 10px;  /* Adds some space around content */
            
        }}
        .navbar .title {{
        font-size: 1.4em;
        font-weight: bold;
        color: white;
        margin-left: 10px;
        margin-top: 70px;
        }}
        .navbar img {{
            height: 35px;
        margin-top: 65px;
        }}
        .footer {{
            font-size: 10px;
            padding: 1px 0;
            text-align: center; /* Center-align text */
            position: fixed;
            bottom: 0;
            left: 0;
            z-index: 1000;
        }}
        .trailer-link {{
            color: #E50914; /* Netflix red */
            font-weight: bold;
            text-decoration: none;
            transition: all 0.3s ease;
        }}

        .trailer-link:hover {{
            color: #B00710; /* Darker Netflix red on hover */
            text-decoration: underline;
        }}

    }}
    </style>
    <div class="footer">
        <h7>Follow us:</h7>
        <p> <a href="https://www.linkedin.com/in/anupnalawade/" target="_blank">LinkedIn</a>
        | <a href="https://github.com/annup7/" target="_blank">GitHub</a>
        | <a href="https://www.instagram.com/anupp.7/" target="_blank">Instagram</a>
        | <a href="https://x.com/AnupNalawade" target="_blank">X</a>
        </p>
    </div>
    <div class="navbar">
        <div style="display: flex; align-items: center;">
            <img src="https://th.bing.com/th/id/OIP.SXcDvjOwHieLf7F--pdfOgHaHa?rs=1&pid=ImgDetMain" alt="Logo" style="height: 35px;">
            <span class="title">Cinexa</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# Main Content
st.markdown('<div class="main">', unsafe_allow_html=True)
st.markdown('<h1 class="custom-title">Find Your Next Favorite Movie!</h1>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

selected_movie_name = st.selectbox(
    'Select a movie to get recommendations:',
    [''] + movies['title'].values.tolist(),  # Empty string as placeholder
)

# Display additional details in recommendations
if selected_movie_name:
    if st.button('Recommend'):
        recommendations = recommend(selected_movie_name)
        st.write("### Recommended Movies:")

        for movie, poster, overview, genres, imdb_rating, trailer_url, cast in recommendations:
            with st.container():
                cols = st.columns([1, 5], gap="small")  # Adjust column width ratios
                with cols[0]:  # Poster Column
                    if poster:
                        st.image(poster, caption=movie, use_container_width=True)
                    else:
                        st.write(f"Poster not available for {movie}")

                with cols[1]:  # Overview Column with Expander
                    st.subheader(f"**{movie}**")
                    st.write(
                        f"<span class='netflix-red'>**Genres:**</span> {genres}", 
                        unsafe_allow_html=True
                    )
                    st.write(
                        f"<span class='netflix-red'>**IMDB Rating:**</span> {imdb_rating}/10", 
                        unsafe_allow_html=True
                    )
                    st.write(
                        f"<span class='netflix-red'>**Cast:**</span> {cast}", 
                        unsafe_allow_html=True
                    )
                    st.write(
                        f"<span class='netflix-red'>**Overview:**</span> {overview}", 
                        unsafe_allow_html=True
                    )

                    if trailer_url:
                        st.markdown(
                             f"""
                            <style>
                                .trailer-link {{
                                    color: #E50914; /* Netflix red */
                                    font-weight: bolder;
                                   
                                    transition: all 0.3s ease;
                                }}
                                .trailer-link:hover {{
                                    color: #B00710; /* Darker Netflix red */
                                    text-decoration: underline;
                                }}
                            </style>
                            <a href="{trailer_url}" class="trailer-link" target="_blank">
                                Click here to Watch Trailer
                            </a>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.write("Trailer not available.")
        conn = connect_to_db()

        # Insert movie recommendations into the database
        insert_movie_recommendations(conn, recommendations)

        # Close the database connection if it was established
        if conn:
            conn.close()


st.markdown("""
    <h4 id="about">About Us:</h4>
    <p>Welcome to Cinexa, your ultimate movie discovery platform. Powered by advanced recommendations, we help you find movies that suit your taste effortlessly. Explore trailers, curated lists, and personalized suggestions to make your movie-watching experience better and more exciting!</p>
""", unsafe_allow_html=True)
