import os
import django
import requests
from pathlib import Path
from django.conf import settings

# Ensure Django settings are loaded
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "my_project.settings")
django.setup()

from django.core.management.base import BaseCommand
from myapp.models import Movie, TVShow
from config import API_KEY, ACCESS_TOKEN

HEADERS = {
    "accept": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}"
}

class Command(BaseCommand):
    """
    Management command to download streaming provider logos from TMDB.
    
    This command fetches all available streaming provider information for a specified region
    and downloads their logos. Logos are stored in the media/providers directory.
    
    Usage:
        python manage.py get_providers_logo
        python manage.py get_providers_logo --region NO
    """
    help = "Download streaming provider logos from TMDB"

    def add_arguments(self, parser):
        parser.add_argument('--region', type=str, default='US',
                           help='Region code for watch providers (default: NO)')

    def download_provider_logo(self, logo_path):
        """
        Download provider logo from TMDB and save it locally.
        
        Args:
            logo_path: Path to the logo on TMDB (e.g., "/path/to/logo.jpg")
            
        Returns:
            Local path to saved logo or None if download failed
        """
        if not logo_path:
            return None

        # Construct the full TMDB image URL
        image_url = f"https://image.tmdb.org/t/p/original{logo_path}"
        
        try:
            response = requests.get(image_url, stream=True)
            if response.status_code != 200:
                self.stdout.write(self.style.WARNING(
                    f"Failed to download logo from {image_url}"
                ))
                return None

            # Create directory for provider logos
            save_dir = Path(settings.MEDIA_ROOT) / 'providers'
            save_dir.mkdir(parents=True, exist_ok=True)

            # Remove leading slash and create local filename
            local_filename = logo_path.lstrip('/')
            file_path = save_dir / local_filename

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Download and save the file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return f'providers/{local_filename}'

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error downloading logo: {str(e)}"))
            return None

    def get_provider_logos(self, region):
        """Fetch all streaming provider information for a region."""
        # Get both movie and TV show providers
        providers = set()
        
        # Fetch movie providers
        movie_url = "https://api.themoviedb.org/3/watch/providers/movie"
        tv_url = "https://api.themoviedb.org/3/watch/providers/tv"
        
        try:
            # Fetch movie providers
            movie_response = requests.get(movie_url, headers=HEADERS)
            if movie_response.status_code == 200:
                movie_data = movie_response.json()
                movie_providers = movie_data.get('results', [])
                if region:
                    movie_providers = [p for p in movie_providers if region in (p.get('display_priorities', {}) or {})]
                providers.update({(p['provider_name'], p['logo_path']) for p in movie_providers if p.get('logo_path')})
            
            # Fetch TV providers
            tv_response = requests.get(tv_url, headers=HEADERS)
            if tv_response.status_code == 200:
                tv_data = tv_response.json()
                tv_providers = tv_data.get('results', [])
                if region:
                    tv_providers = [p for p in tv_providers if region in (p.get('display_priorities', {}) or {})]
                providers.update({(p['provider_name'], p['logo_path']) for p in tv_providers if p.get('logo_path')})
            
            return [{'provider_name': name, 'logo_path': logo} for name, logo in providers]

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error fetching providers: {str(e)}"))
            return []

    def handle(self, *args, **options):
        """Main execution method."""
        region = options['region']
        
        self.stdout.write(f"Fetching provider information for region: {region}")
        
        # Get all providers
        providers = self.get_provider_logos(region)
        
        if not providers:
            self.stdout.write(self.style.ERROR("No providers found!"))
            return

        self.stdout.write(f"Found {len(providers)} unique providers. Downloading logos...")
        
        downloaded = 0
        skipped = 0
        failed = 0
        
        # Download logos for each provider
        for provider in providers:
            logo_path = provider.get('logo_path')
            provider_name = provider.get('provider_name', 'Unknown Provider')
            
            if not logo_path:
                self.stdout.write(self.style.WARNING(
                    f"No logo path for provider: {provider_name}"
                ))
                skipped += 1
                continue

            # Check if logo already exists
            local_path = Path(settings.MEDIA_ROOT) / 'providers' / logo_path.lstrip('/')
            if local_path.exists():
                self.stdout.write(self.style.WARNING(
                    f"Logo for {provider_name} already exists, skipping..."
                ))
                skipped += 1
                continue

            self.stdout.write(f"Downloading logo for: {provider_name}")
            local_path = self.download_provider_logo(logo_path)
            
            if local_path:
                downloaded += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Successfully downloaded logo for {provider_name}"
                ))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR(
                    f"Failed to download logo for {provider_name}"
                ))

        self.stdout.write(self.style.SUCCESS(
            f"\nProvider logos download complete!\n"
            f"Downloaded: {downloaded}\n"
            f"Skipped: {skipped}\n"
            f"Failed: {failed}"
        ))