from django.core.management.base import BaseCommand
import requests

from myapp.models import Genre
from config import API_KEY

class Command(BaseCommand):
    help = "Populate the Genre table with data from TMDB."

    def handle(self, *args, **options):
        url = f"https://api.themoviedb.org/3/genre/movie/list"
        params = {
            "api_key": API_KEY,
            "language": "en-US"
        }
        response = requests.get(url, params=params)
        data = response.json()

        genres_data = data.get("genres", [])
        if not genres_data:
            self.stdout.write(self.style.WARNING("No genres received from TMDB."))
            return

        for g in genres_data:
            # g is a dict with keys "id" and "name"
            tmdb_id = g.get("id")
            genre_name = g.get("name")
            if tmdb_id and genre_name:
                _, created = Genre.objects.update_or_create(
                    tmdb_id=tmdb_id,
                    defaults={"name": genre_name}
                )
                if created:
                    self.stdout.write(f"Created new genre: {genre_name}")
                else:
                    self.stdout.write(f"Updated existing genre: {genre_name}")

        self.stdout.write(self.style.SUCCESS("Successfully populated genres!"))