import os
import requests
import django
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from myapp.models import Movie, TVShow, Genre
from config import API_KEY, ACCESS_TOKEN

# Ensure Django settings are loaded
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project.settings")
django.setup()

HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

class Command(BaseCommand):
    help = "Update detailed information for movies and TV shows"

    def add_arguments(self, parser):
        parser.add_argument(
            '--media-type',
            type=str,
            choices=['movie', 'tv', 'both'],
            default='both',
            help='Type of media to update: movie, tv, or both'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of items to update'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Only update items older than this many days'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update all items regardless of last update time'
        )

    def get_or_create_genres(self, genre_ids):
        """Get or create genres for the given genre IDs."""
        genres = []
        for genre_data in genre_ids:
            genre, created = Genre.objects.get_or_create(
                tmdb_id=genre_data['id'],
                defaults={'name': genre_data['name']}
            )
            genres.append(genre)
        return genres
    def fetch_movie_details(self, movie_id):
        """Fetch detailed information for a movie."""
        url = f"https://api.themoviedb.org/3/movie/{movie_id}"
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"Failed to fetch details for movie ID {movie_id}: {str(e)}"
            ))
            return None
        
    def fetch_tv_details(self, tv_id):
        """Fetch detailed information for a TV show."""
        url = f"https://api.themoviedb.org/3/tv/{tv_id}"
        try:
            response = requests.get(url, headers=HEADERS)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"Failed to fetch details for TV show ID {tv_id}: {str(e)}"
            ))
            return None
        
    @transaction.atomic
    def update_movie_details(self, days, limit, force=False):
        """Update detailed information for movies."""
        queryset = Movie.objects.all().order_by('-popularity')
        
        if days and not force:
            cutoff_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(updated_at__lte=cutoff_date)
        
        if limit:
            queryset = queryset[:limit]
            
        total = queryset.count()
        self.stdout.write(f"Updating details for {total} movies...")
        
        updated = skipped = 0
        
        for movie in queryset:
            self.stdout.write(f"Fetching details for movie: {movie.title}")
            details = self.fetch_movie_details(movie.tmdb_id)
            
            if not details:
                skipped += 1
                continue
                
            try:
                with transaction.atomic():
                    # Update movie with additional details
                    movie.runtime = details.get('runtime')
                    movie.rating = details.get('vote_average', movie.rating)
                    movie.vote_count = details.get('vote_count', movie.vote_count)
                    movie.popularity = details.get('popularity', movie.popularity)
                    movie.overview = details.get('overview') or movie.overview
                    
                    # Update genres
                    if details.get('genres'):
                        genres = self.get_or_create_genres(details['genres'])
                        movie.genres.set(genres)
                    
                    movie.save()
                    updated += 1
                    
                    if updated % 10 == 0:
                        self.stdout.write(f"Updated {updated}/{total} movies...")
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error updating movie {movie.title}: {str(e)}"
                ))
                skipped += 1
                
        return updated, skipped
        
    @transaction.atomic
    def update_tv_details(self, days, limit, force=False):
        """Update detailed information for TV shows."""
        queryset = TVShow.objects.all().order_by('-popularity')
        
        if days and not force:
            cutoff_date = timezone.now() - timedelta(days=days)
            queryset = queryset.filter(updated_at__lte=cutoff_date)
        
        if limit:
            queryset = queryset[:limit]
            
        total = queryset.count()
        self.stdout.write(f"Updating details for {total} TV shows...")
        
        updated = skipped = 0
        
        for show in queryset:
            self.stdout.write(f"Fetching details for TV show: {show.title}")
            details = self.fetch_tv_details(show.tmdb_id)
            
            if not details:
                skipped += 1
                continue
                
            try:
                with transaction.atomic():
                    # Update TV show with additional details
                    show.episode_run_time = details.get('episode_run_time', [])
                    show.number_of_seasons = details.get('number_of_seasons')
                    show.number_of_episodes = details.get('number_of_episodes')
                    show.first_air_date = details.get('first_air_date')
                    show.last_air_date = details.get('last_air_date')
                    show.rating = details.get('vote_average', show.rating)
                    show.vote_count = details.get('vote_count', show.vote_count)
                    show.popularity = details.get('popularity', show.popularity)
                    show.overview = details.get('overview') or show.overview
                    
                    # Update genres
                    if details.get('genres'):
                        genres = self.get_or_create_genres(details['genres'])
                        show.genres.set(genres)
                    
                    show.save()
                    updated += 1
                    
                    if updated % 10 == 0:
                        self.stdout.write(f"Updated {updated}/{total} TV shows...")
            
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Error updating TV show {show.title}: {str(e)}"
                ))
                skipped += 1
                
        return updated, skipped

    def handle(self, *args, **options):
        """Main execution method."""
        start_time = timezone.now()
        
        media_type = options['media_type']
        limit = options['limit']
        days = options['days']
        force = options['force']
        
        movie_updated = tv_updated = 0
        movie_skipped = tv_skipped = 0
        
        try:
            if media_type in ['movie', 'both']:
                movie_updated, movie_skipped = self.update_movie_details(days, limit, force)
                
            if media_type in ['tv', 'both']:
                tv_updated, tv_skipped = self.update_tv_details(days, limit, force)
                
            duration = timezone.now() - start_time
            
            self.stdout.write(self.style.SUCCESS(
                f"\nDetails update complete in {duration}!\n"
                f"Movies: {movie_updated} updated, {movie_skipped} skipped\n"
                f"TV Shows: {tv_updated} updated, {tv_skipped} skipped"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during update: {str(e)}"))