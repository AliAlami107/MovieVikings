from django.core.management.base import BaseCommand
from myapp.models import Badge

class Command(BaseCommand):
    help = "Create initial achievement badges"

    def handle(self, *args, **options):
        # Milestone badges for movies watched
        milestone_badges = [
            {
                'name': 'Movie Beginner',
                'description': 'Watch 5 movies',
                'badge_type': 'milestone',
                'rarity': 'bronze',
                'icon': '🎬',
                'requirement_count': 5,
                'requirement_type': 'movies_watched',
            },
            {
                'name': 'Movie Enthusiast',
                'description': 'Watch 20 movies',
                'badge_type': 'milestone',
                'rarity': 'silver',
                'icon': '🎬',
                'requirement_count': 20,
                'requirement_type': 'movies_watched',
            },
            {
                'name': 'Movie Expert',
                'description': 'Watch 50 movies',
                'badge_type': 'milestone',
                'rarity': 'gold',
                'icon': '🎬',
                'requirement_count': 50,
                'requirement_type': 'movies_watched',
            },
            {
                'name': 'Movie Master',
                'description': 'Watch 100 movies',
                'badge_type': 'milestone',
                'rarity': 'platinum',
                'icon': '🎬',
                'requirement_count': 100,
                'requirement_type': 'movies_watched',
            },
            # TV Show badges
            {
                'name': 'TV Show Beginner',
                'description': 'Watch 3 TV shows',
                'badge_type': 'milestone',
                'rarity': 'bronze',
                'icon': '📺',
                'requirement_count': 3,
                'requirement_type': 'tv_shows_watched',
            },
            {
                'name': 'TV Show Enthusiast',
                'description': 'Watch 10 TV shows',
                'badge_type': 'milestone',
                'rarity': 'silver',
                'icon': '📺',
                'requirement_count': 10,
                'requirement_type': 'tv_shows_watched',
            },
            {
                'name': 'TV Show Expert',
                'description': 'Watch 25 TV shows',
                'badge_type': 'milestone',
                'rarity': 'gold',
                'icon': '📺',
                'requirement_count': 25,
                'requirement_type': 'tv_shows_watched',
            },
            {
                'name': 'TV Show Master',
                'description': 'Watch 50 TV shows',
                'badge_type': 'milestone',
                'rarity': 'platinum',
                'icon': '📺',
                'requirement_count': 50,
                'requirement_type': 'tv_shows_watched',
            },
            # Review badges
            {
                'name': 'Critic Beginner',
                'description': 'Write 3 reviews',
                'badge_type': 'critic',
                'rarity': 'bronze',
                'icon': '✍️',
                'requirement_count': 3,
                'requirement_type': 'reviews_written',
            },
            {
                'name': 'Critic Enthusiast',
                'description': 'Write 10 reviews',
                'badge_type': 'critic',
                'rarity': 'silver',
                'icon': '✍️',
                'requirement_count': 10,
                'requirement_type': 'reviews_written',
            },
            {
                'name': 'Critic Expert',
                'description': 'Write 25 reviews',
                'badge_type': 'critic',
                'rarity': 'gold',
                'icon': '✍️',
                'requirement_count': 25,
                'requirement_type': 'reviews_written',
            },
            # Total watch time badges
            {
                'name': 'Viewer Beginner',
                'description': 'Watch 24 hours of content',
                'badge_type': 'milestone',
                'rarity': 'bronze',
                'icon': '⏱️',
                'requirement_count': 24,
                'requirement_type': 'watch_hours',
            },
            {
                'name': 'Viewer Enthusiast',
                'description': 'Watch 72 hours of content',
                'badge_type': 'milestone',
                'rarity': 'silver',
                'icon': '⏱️',
                'requirement_count': 72,
                'requirement_type': 'watch_hours',
            },
            {
                'name': 'Viewer Expert',
                'description': 'Watch 150 hours of content',
                'badge_type': 'milestone',
                'rarity': 'gold',
                'icon': '⏱️',
                'requirement_count': 150,
                'requirement_type': 'watch_hours',
            },
            {
                'name': 'Viewer Master',
                'description': 'Watch 300 hours of content',
                'badge_type': 'milestone',
                'rarity': 'platinum',
                'icon': '⏱️',
                'requirement_count': 300,
                'requirement_type': 'watch_hours',
            },
        ]
        
        badges_created = 0
        badges_updated = 0
        
        for badge_data in milestone_badges:
            badge, created = Badge.objects.update_or_create(
                name=badge_data['name'],
                defaults=badge_data
            )
            
            if created:
                badges_created += 1
                self.stdout.write(self.style.SUCCESS(f"Created badge: {badge.name}"))
            else:
                badges_updated += 1
                self.stdout.write(f"Updated badge: {badge.name}")
                
        self.stdout.write(self.style.SUCCESS(f"Badges created: {badges_created}, updated: {badges_updated}")) 