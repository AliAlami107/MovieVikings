"""
Django models for the MovieVikings application.

This module contains all database models used in the application, including user management,
content tracking, and social features.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q

# Available regions for content availability and streaming services
REGION_CHOICES = [
    ('NO', 'Norway'),
    ('US', 'United States'),
    ('GB', 'United Kingdom'),
    ('DE', 'Germany'),
    ('FR', 'France'),
    ('SE', 'Sweden'),
    ('DK', 'Denmark'),
]

class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    
    Adds functionality for:
    - Streaming service preferences
    - Favorite movies and TV shows
    - Social features (friends, friend requests)
    """
    
    streaming_services = models.ManyToManyField(
        'streamingservice',
        related_name='users',
        blank=True,
        help_text='Streaming services the user has access to'
    )

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    favorite_movies = models.ManyToManyField('Movie', related_name='favorited_by', blank=True)
    favorite_shows = models.ManyToManyField('TVShow', related_name='favorited_by', blank=True)

    def send_friend_request(self, to_user):
        """Send a friend request to another user"""
        if to_user == self:
            return False  # Can't friend yourself
        
        # Check if request already exists
        existing_request = FriendRequest.objects.filter(
            (Q(from_user=self) & Q(to_user=to_user)) | 
            (Q(from_user=to_user) & Q(to_user=self))
        ).first()
        
        if existing_request:
            return False  # Request already exists
        
        # Create new request
        FriendRequest.objects.create(from_user=self, to_user=to_user)
        return True

    def accept_friend_request(self, from_user):
        """Accept a friend request from another user"""
        try:
            request = FriendRequest.objects.get(from_user=from_user, to_user=self, status='pending')
            request.status = 'accepted'
            request.save()
            return True
        except FriendRequest.DoesNotExist:
            return False

    def reject_friend_request(self, from_user):
        """Reject a friend request from another user"""
        try:
            request = FriendRequest.objects.get(from_user=from_user, to_user=self, status='pending')
            request.status = 'rejected'
            request.save()
            return True
        except FriendRequest.DoesNotExist:
            return False

    def unfriend(self, user):
        """Remove friendship with another user"""
        # Find and delete any accepted requests between these users
        FriendRequest.objects.filter(
            ((Q(from_user=self) & Q(to_user=user)) | 
            (Q(from_user=user) & Q(to_user=self))) &
            Q(status='accepted')
        ).delete()
        
        # Also make sure to delete any pending or rejected requests
        # so users can send new friend requests
        FriendRequest.objects.filter(
            (Q(from_user=self) & Q(to_user=user)) | 
            (Q(from_user=user) & Q(to_user=self))
        ).delete()
        
        return True

    def get_friends(self):
        """Get all friends for this user"""
        accepted_sent = FriendRequest.objects.filter(
            from_user=self, status='accepted'
        ).values_list('to_user', flat=True)
        
        accepted_received = FriendRequest.objects.filter(
            to_user=self, status='accepted'
        ).values_list('from_user', flat=True)
        
        friend_ids = list(accepted_sent) + list(accepted_received)
        return User.objects.filter(id__in=friend_ids)

    def get_pending_requests(self):
        """Get all pending friend requests received by this user"""
        return FriendRequest.objects.filter(
            to_user=self, status='pending'
        )

class Genre(models.Model):
    """
    A model representing a single genre that can be associated with many movies or TV shows.
    """
    tmdb_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class BaseContent(models.Model):
    """
    Abstract base model for movie and TV show content.
    
    Contains common fields and functionality shared between movies and TV shows.
    This model is not meant to be used directly, but rather inherited by Movie and TVShow models.
    """
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField(null=True, blank=True)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    popularity = models.FloatField(default=0.0)
    rating = models.FloatField(default=0.0)
    vote_count = models.IntegerField(default=0)
    genres = models.ManyToManyField(Genre, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Movie(BaseContent):
    """
    Model representing a movie in the system.
    
    Extends BaseContent with movie-specific fields and functionality.
    Includes streaming availability information and runtime details.
    """
    class Meta:
        indexes = [
            models.Index(fields=['-popularity']),
            models.Index(fields=['-rating']),
            models.Index(fields=['release_date']),
            models.Index(fields=['title']),  # For search
            models.Index(fields=['-created_at']),
        ]
    release_date = models.DateField(null=True, blank=True)
    runtime = models.IntegerField(null=True, blank=True)

    @property
    def get_providers(self, region='NO'):
        return {
            'flatrate': self.streaming_info.filter(
                region=region, 
                type='flatrate'
            ).select_related('provider'),
            'rent': self.streaming_info.filter(
                region=region, 
                type='rent'
            ).select_related('provider'),
            'buy': self.streaming_info.filter(
                region=region, 
                type='buy'
            ).select_related('provider'),
        }

    def __str__(self):
        return f"{self.title} ({self.release_date.year if self.release_date else 'N/A'})"
    
class TVShow(BaseContent):
    """
    Model representing a TV show in the system.
    
    Extends BaseContent with TV show-specific fields and functionality.
    Includes episode information, air dates, and season details.
    """
    class Meta:
        indexes = [
            models.Index(fields=['-popularity']),
            models.Index(fields=['-rating']),
            models.Index(fields=['first_air_date']),
            models.Index(fields=['title']),
            models.Index(fields=['-created_at']),
        ]
    first_air_date = models.DateField(null=True, blank=True)
    last_air_date = models.DateField(null=True, blank=True)
    number_of_seasons = models.IntegerField(null=True, blank=True)
    number_of_episodes = models.IntegerField(null=True, blank=True)
    episode_run_time = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.first_air_date.year if self.first_air_date else 'N/A'})"
    
class WatchlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist_items')
    title = models.CharField(max_length=200)
    media_id = models.CharField(max_length=50)  # TMDB ID
    media_type = models.CharField(max_length=10)  # 'movie' or 'tv'
    poster_path = models.CharField(max_length=200, null=True, blank=True)
    added_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'media_id', 'media_type')  # Prevent duplicates

    def __str__(self):
        return f"{self.user.username}'s watchlist - {self.title}"
    
class StreamingProvider(models.Model):
    """
    Model representing a streaming service provider.
    
    Stores information about streaming services including their TMDB ID,
    display name, and logo path for UI representation.
    """
    name = models.CharField(max_length=100)
    tmdb_id = models.IntegerField(unique=True)
    logo_path = models.CharField(max_length=255)
    display_priority = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
class BaseProvider(models.Model):
    """
    Abstract base model for content providers.
    
    Contains common fields and functionality for both movie and TV show providers.
    This model is not meant to be used directly, but rather inherited by MovieProvider and TVShowProvider models.
    """
    provider = models.ForeignKey(StreamingProvider, on_delete=models.CASCADE)
    region = models.CharField(
        max_length=2,
        choices=REGION_CHOICES,
        default='NO',
        help_text='Region code for content availability'
    )
    type = models.CharField(max_length=20, choices=[
        ('flatrate', 'Streaming'),
        ('rent', 'Rent'),
        ('buy', 'Buy'),
    ])
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['region', 'type']),
        ]

class MovieProvider(BaseProvider):
    movie = models.ForeignKey('Movie', on_delete=models.CASCADE, related_name='streaming_info')

    class Meta:
        unique_together = ['movie', 'provider', 'region', 'type']
        indexes = [
            models.Index(fields=['region', 'type']),
            models.Index(fields=['movie', 'region']),
        ]
        verbose_name = 'Movie Provider'
        verbose_name_plural = 'Movie Providers'

class TVShowProvider(BaseProvider):
    tv_show = models.ForeignKey('TVShow', on_delete=models.CASCADE, related_name='streaming_info')

    class Meta:
        unique_together = ['tv_show', 'provider', 'region', 'type']
        indexes = [
            models.Index(fields=['region', 'type']),
            models.Index(fields=['tv_show', 'region']),
        ]
        verbose_name = 'TV Show Provider'
        verbose_name_plural = 'TV Show Providers'

class StreamingService(models.Model): 
    name = models.CharField(max_length=100, unique=True)

    def __str__(self): 
        return self.name

class WatchedMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watched_movies')
    media_id = models.CharField(max_length=50)  # TMDB ID
    media_type = models.CharField(max_length=10, choices=[('movie', 'Movie'), ('tv', 'TV Show')])
    title = models.CharField(max_length=255)
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    rating = models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], null=True, blank=True)
    watched_date = models.DateTimeField(auto_now_add=True)
    runtime = models.IntegerField(null=True, blank=True)  # Store runtime in minutes
    rated_date = models.DateTimeField(null=True, blank=True)
    review = models.TextField(null=True, blank=True) 

    class Meta:
        unique_together = ('user', 'media_id', 'media_type')
        
    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.media_type})"

class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    from_user = models.ForeignKey(User, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friend_requests_received', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('from_user', 'to_user')
    
    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({self.status})"

class Badge(models.Model):
    """Model for achievement badges that users can earn."""
    BADGE_TYPES = (
        ('milestone', 'Milestone Badge'),
        ('genre', 'Genre Specialist'),
        ('critic', 'Critic Badge'),
        ('explorer', 'Explorer Badge'),
    )
    
    BADGE_RARITIES = (
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('platinum', 'Platinum'),
    )
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    rarity = models.CharField(max_length=20, choices=BADGE_RARITIES, default='bronze')
    icon = models.CharField(max_length=100, help_text="Font awesome icon class or emoji")
    requirement_count = models.IntegerField(default=0, help_text="Number required to earn this badge (e.g., 10 movies)")
    requirement_type = models.CharField(max_length=50, help_text="Type of requirement (e.g., 'movies_watched', 'reviews')")
    
    def __str__(self):
        return f"{self.name} ({self.get_rarity_display()})"

class UserBadge(models.Model):
    """Model for tracking which badges users have earned."""
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'badge')
        
    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"
