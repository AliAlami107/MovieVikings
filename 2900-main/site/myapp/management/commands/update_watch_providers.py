from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import transaction
from django.db.models import Q
from myapp.models import Movie, TVShow, StreamingProvider, MovieProvider, TVShowProvider
from config import API_KEY, ACCESS_TOKEN
import requests

HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}
# Add this at the class level
class Command(BaseCommand):
    help = "Update streaming providers for movies and TV shows"
    ALLOWED_REGIONS = ['NO', 'US', 'GB', 'DE', 'FR', 'SE', 'DK'] 
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
            default=7,
            help='Only update items whose providers are older than this many days'
        )
    def get_or_create_provider(self, provider_data):
        """Get or create a streaming provider."""
        provider, created = StreamingProvider.objects.get_or_create(
            tmdb_id=provider_data['provider_id'],
            defaults={
                'name': provider_data['provider_name'],
                'logo_path': provider_data.get('logo_path', ''),
                'display_priority': provider_data.get('display_priority', 0)
            }
        )
        return provider

    def fetch_watch_providers(self, media_type, media_id):
        """Fetch streaming providers for a movie or TV show."""
        url = f"https://api.themoviedb.org/3/{media_type}/{media_id}/watch/providers"
        
        try:
            response = requests.get(url, headers=HEADERS)
            self.stdout.write(f"Fetching providers for {media_type} ID {media_id}")
            
            if response.status_code != 200:
                self.stdout.write(self.style.WARNING(
                    f"Failed to fetch providers for {media_type} ID {media_id}"
                ))
                return {}
                
            return response.json().get("results", {})
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Error fetching providers for {media_type} ID {media_id}: {str(e)}"
            ))
            return {}

    @transaction.atomic
    def update_movie_providers(self, movie, providers_data):
        """Update providers for a single movie."""
        try:
            # Clear existing providers for this movie
            MovieProvider.objects.filter(movie=movie).delete()
            
            for region, region_data in providers_data.items():
                # Only process allowed regions
                if region not in self.ALLOWED_REGIONS:
                    continue
                # Process flatrate (streaming) providers
                for provider_data in region_data.get('flatrate', []):
                    provider = self.get_or_create_provider(provider_data)
                    MovieProvider.objects.create(
                        movie=movie,
                        provider=provider,
                        region=region,
                        type='flatrate'
                    )

                # Process rent providers
                for provider_data in region_data.get('rent', []):
                    provider = self.get_or_create_provider(provider_data)
                    MovieProvider.objects.create(
                        movie=movie,
                        provider=provider,
                        region=region,
                        type='rent'
                    )

                # Process buy providers
                for provider_data in region_data.get('buy', []):
                    provider = self.get_or_create_provider(provider_data)
                    MovieProvider.objects.create(
                        movie=movie,
                        provider=provider,
                        region=region,
                        type='buy'
                    )
            
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating providers for movie {movie.title}: {str(e)}"))
            return False

    @transaction.atomic
    def update_tv_providers(self, show, providers_data):
        """Update providers for a single TV show."""
        try:
            # Clear existing providers for this show
            TVShowProvider.objects.filter(tv_show=show).delete()
            
            for region, region_data in providers_data.items():
                # Only process allowed regions
                if region not in self.ALLOWED_REGIONS:
                    continue
                # Process flatrate (streaming) providers
                for provider_data in region_data.get('flatrate', []):
                    provider = self.get_or_create_provider(provider_data)
                    TVShowProvider.objects.create(
                        tv_show=show,
                        provider=provider,
                        region=region,
                        type='flatrate'
                    )

                # Process rent providers
                for provider_data in region_data.get('rent', []):
                    provider = self.get_or_create_provider(provider_data)
                    TVShowProvider.objects.create(
                        tv_show=show,
                        provider=provider,
                        region=region,
                        type='rent'
                    )

                # Process buy providers
                for provider_data in region_data.get('buy', []):
                    provider = self.get_or_create_provider(provider_data)
                    TVShowProvider.objects.create(
                        tv_show=show,
                        provider=provider,
                        region=region,
                        type='buy'
                    )
            
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating providers for show {show.title}: {str(e)}"))
            return False

    def handle(self, *args, **options):
        """Main execution method."""
        start_time = timezone.now()
        media_type = options['media_type']
        limit = options['limit']
        days = options['days']
        
        cutoff_date = timezone.now() - timedelta(days=days) if days else None
        
        updated = skipped = 0
        
        try:
            # Update movies
            if media_type in ['movie', 'both']:
                movies = Movie.objects.all().order_by('-popularity')
                if limit:
                    movies = movies[:limit]
                
                total_movies = movies.count()
                self.stdout.write(f"Processing {total_movies} movies...")
                
                for movie in movies:
                    self.stdout.write(f"Fetching providers for movie: {movie.title}")
                    providers_data = self.fetch_watch_providers('movie', movie.tmdb_id)
                    
                    if providers_data and self.update_movie_providers(movie, providers_data):
                        updated += 1
                    else:
                        skipped += 1
                    
                    if updated % 10 == 0:
                        self.stdout.write(f"Processed {updated + skipped}/{total_movies} movies...")

            # Update TV shows
            if media_type in ['tv', 'both']:
                tv_shows = TVShow.objects.all().order_by('-popularity')
                if limit:
                    tv_shows = tv_shows[:limit]
                
                total_shows = tv_shows.count()
                self.stdout.write(f"Processing {total_shows} TV shows...")
                
                for show in tv_shows:
                    self.stdout.write(f"Fetching providers for TV show: {show.title}")
                    providers_data = self.fetch_watch_providers('tv', show.tmdb_id)
                    
                    if providers_data and self.update_tv_providers(show, providers_data):
                        updated += 1
                    else:
                        skipped += 1
                    
                    if updated % 10 == 0:
                        self.stdout.write(f"Processed {updated + skipped}/{total_shows} TV shows...")

            duration = timezone.now() - start_time
            self.stdout.write(self.style.SUCCESS(
                f"\nProviders update complete in {duration}!\n"
                f"Updated: {updated}\n"
                f"Skipped: {skipped}"
            ))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during update: {str(e)}"))