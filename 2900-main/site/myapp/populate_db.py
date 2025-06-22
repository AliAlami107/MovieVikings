import requests
import os
import django
from config import API_KEY

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project.settings")
django.setup()

from myapp.models import Movie  # Import your model

# TMDB API details
BASE_URL = "https://api.themoviedb.org/3"

def fetch_movies():
    """Fetch popular movies available in Norway from TMDB."""
    url = f"{BASE_URL}/movie/popular?api_key={API_KEY}&language=en-US&region=NO"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get("results", [])
    else:
        print(f"Error fetching movies: {response.status_code}")
        return []

def populate_movies():
    """Save fetched movies into SQLite database."""
    movies = fetch_movies()

    for movie in movies:
        Movie.objects.update_or_create(
            tmdb_id=movie["id"],  # Use TMDB ID to avoid duplicates
            defaults={
                "title": movie["title"],
                "release_date": movie["release_date"],
                "overview": movie["overview"],
                "popularity": movie["popularity"],
                "poster_path": movie["poster_path"],
            }
        )
    print(f"Successfully added {len(movies)} movies to the database.")

if __name__ == "__main__":
    populate_movies()