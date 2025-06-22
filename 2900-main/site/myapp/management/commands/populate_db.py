import os
import requests
import django
from django.core.management.base import BaseCommand
from django.conf import settings
from myapp.models import Movie, TVShow, Genre
from dotenv import load_dotenv

# Ensure Django settings are loaded
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project.settings")
django.setup()

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
ACCESS_TOKEN = os.getenv("TMDB_ACCESS_TOKEN")

HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

class Command(BaseCommand):
    help = "Populate database with popular movies and TV shows from TMDB"

    def add_arguments(self, parser):
        parser.add_argument('--media-type', type=str, choices=['movie', 'tv', 'both'], default='both',
                            help='Type of media to fetch: movie, tv, or both')
        parser.add_argument('--pages', type=int, default=5, 
                            help='Number of pages to fetch for each media type')

    def fetch_popular_media(self, media_type, page):
        """
        Fetch popular movies or TV shows from TMDB.
        
        Args:
            media_type: 'movie' or 'tv'
            page: Page number to fetch
            
        Returns:
            List of media objects (dicts)
        """
        url = (
            f"https://api.themoviedb.org/3/{media_type}/popular"
            f"?api_key={API_KEY}&language=en-US&page={page}"
        )
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("results", [])
        
        self.stdout.write(self.style.WARNING(
            f"Failed to fetch {media_type} data for page {page}: {response.status_code}"
        ))
        return []
        
    def download_poster(self, poster_path):
        """
        Download the poster from TMDB and store it locally.
        
        Args:
            poster_path: Poster path from TMDB (e.g., "/abcd123.jpg")
            
        Returns:
            String with local path or None if download failed
        """
        if not poster_path:
            return None

        # Construct the full TMDB image URL
        image_url = f"https://image.tmdb.org/t/p/w500{poster_path}"
        response = requests.get(image_url, stream=True)
        if response.status_code != 200:
            self.stdout.write(self.style.WARNING(
                f"Failed to download poster from {image_url}"
            ))
            return None

        # Remove leading slash from poster_path
        local_filename = poster_path.lstrip("/")
        save_dir = os.path.join(settings.MEDIA_ROOT, "posters")
        os.makedirs(save_dir, exist_ok=True)

        file_path = os.path.join(save_dir, local_filename)

        # Download and write file to disk
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        # Return the path relative to MEDIA_ROOT
        return f"posters/{local_filename}"

    def get_or_create_genres(self, genre_ids):
        """Get or create genres for the given genre IDs."""
        genres = []
        for g_id in genre_ids:
            try:
                genre = Genre.objects.get(tmdb_id=g_id)
            except Genre.DoesNotExist:
                genre = Genre.objects.create(tmdb_id=g_id, name="Unknown")
            genres.append(genre)
        return genres

    def handle_movies(self, pages):
        """Fetch and store popular movies."""
        self.stdout.write("Fetching popular movies...")
        movie_count = 0
        
        for page in range(1, pages + 1):
            self.stdout.write(f"Fetching movie page {page} of {pages}...")
            movies = self.fetch_popular_media('movie', page)
            
            for movie_data in movies:
                # Check if we already have basic info for this movie
                existing = Movie.objects.filter(tmdb_id=movie_data["id"]).first()
                if existing and existing.title and existing.overview:
                    continue
                
                # Process poster
                remote_poster_path = movie_data.get("poster_path")
                local_poster_path = self.download_poster(remote_poster_path)
                final_poster_path = local_poster_path or remote_poster_path
                
                # Create or update movie
                release_date = movie_data.get("release_date")
                if release_date == "":
                    release_date = None
                    
                movie_obj, created = Movie.objects.update_or_create(
                    tmdb_id=movie_data["id"],
                    defaults={
                        "title": movie_data.get("title", "Unknown"),
                        "release_date": release_date,
                        "overview": movie_data.get("overview", ""),
                        "popularity": movie_data.get("popularity", 0.0),
                        "rating": movie_data.get("vote_average", 0.0),
                        "vote_count": movie_data.get("vote_count", 0),
                        "poster_path": final_poster_path,
                    }
                )
                
                # Add genres
                genre_ids = movie_data.get("genre_ids", [])
                if genre_ids:
                    genres = self.get_or_create_genres(genre_ids)
                    movie_obj.genres.set(genres)
                
                status = "Added" if created else "Updated"
                self.stdout.write(f"{status}: {movie_obj.title}")
                movie_count += 1
                
        return movie_count

    def handle_tv_shows(self, pages):
        """Fetch and store popular TV shows."""
        self.stdout.write("Fetching popular TV shows...")
        tv_count = 0
        
        for page in range(1, pages + 1):
            self.stdout.write(f"Fetching TV show page {page} of {pages}...")
            shows = self.fetch_popular_media('tv', page)
            
            for show_data in shows:
                # Check if we already have basic info for this show
                existing = TVShow.objects.filter(tmdb_id=show_data["id"]).first()
                if existing and existing.title and existing.overview:
                    continue
                
                # Process poster
                remote_poster_path = show_data.get("poster_path")
                local_poster_path = self.download_poster(remote_poster_path)
                final_poster_path = local_poster_path or remote_poster_path
                
                # Create or update TV show
                show_obj, created = TVShow.objects.update_or_create(
                    tmdb_id=show_data["id"],
                    defaults={
                        "title": show_data.get("name", "Unknown"),  # TV shows use 'name' instead of 'title'
                        "overview": show_data.get("overview", ""),
                        "popularity": show_data.get("popularity", 0.0),
                        "rating": show_data.get("vote_average", 0.0),
                        "vote_count": show_data.get("vote_count", 0),
                        "poster_path": final_poster_path,
                    }
                )
                
                # Add genres
                genre_ids = show_data.get("genre_ids", [])
                if genre_ids:
                    genres = self.get_or_create_genres(genre_ids)
                    show_obj.genres.set(genres)
                
                status = "Added" if created else "Updated"
                self.stdout.write(f"{status}: {show_obj.title}")
                tv_count += 1
                
        return tv_count

    def handle(self, *args, **options):
        """Main execution method for the command."""
        media_type = options['media_type']
        pages = options['pages']
        
        movie_count = 0
        tv_count = 0
        
        if media_type in ['movie', 'both']:
            movie_count = self.handle_movies(pages)
            
        if media_type in ['tv', 'both']:
            tv_count = self.handle_tv_shows(pages)
            
        self.stdout.write(self.style.SUCCESS(
            f"Import complete! Added/updated {movie_count} movies and {tv_count} TV shows."
        ))