from django.test import TestCase, Client
from django.urls import reverse
from .tmdb_client import TMDBClient
from unittest.mock import patch, MagicMock, ANY, call
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.conf import settings
from django.core.paginator import Paginator, Page
from allauth.socialaccount.models import SocialApp
from django.http import HttpRequest, QueryDict
from .models import FriendRequest, WatchedMovie, WatchlistItem, Badge, UserBadge, REGION_CHOICES
import os
from myapp.utils import (
    get_provider_logo_url,
    encode_filters_for_pagination,
    paginate_results,
    _extract_providers_for_item,
    process_content_item
)
User = get_user_model()
# Create your tests here.
class IndexViewTest(TestCase):
    def test_index_view(self):
        url = reverse('index')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
class TMDBClientTests(TestCase):
    def setUp(self):
        self.client = TMDBClient()
    @patch.dict(os.environ, {"TMDB_ACCESS_TOKEN": "fake_token"}, clear=True)
    def test_init_with_token_sets_access_token(self):
        """
        Tests that TMDBClient.__init__ properly sets the access_token if 
        TMDB_ACCESS_TOKEN is found in environment variables.
        """
        client = TMDBClient()
        self.assertIsNotNone(client.access_token)
        self.assertEqual(client.access_token, "fake_token")
    @patch.dict(os.environ, {"TMDB_ACCESS_TOKEN": "fake_token"}, clear=True)
    def test_init_with_token_sets_headers(self):
        """
        Tests that TMDBClient.__init__ sets the Authorization header 
        when TMDB_ACCESS_TOKEN is present.
        """
        client = TMDBClient()
        self.assertIn("Authorization", client.headers)
        self.assertEqual(client.headers["Authorization"], "Bearer fake_token")
    @patch.dict(os.environ, {}, clear=True)
    def test_init_raises_value_error_if_no_keys(self):
        """
        Tests that TMDBClient.__init__ raises a ValueError if neither 
        TMDB_API_KEY nor TMDB_ACCESS_TOKEN is set in environment variables.
        """
        with self.assertRaises(ValueError) as context:
            TMDBClient()
        self.assertIn("Either TMDB_API_KEY or TMDB_ACCESS_TOKEN must be set", str(context.exception))
    @patch.dict(os.environ, {"TMDB_API_KEY": "fake_api_key"}, clear=True)
    @patch("requests.get")
    def test_make_request_with_api_key(self, mock_get):
        """
        Tests that _make_request appends the 'api_key' parameter 
        when TMDB_API_KEY is available.
        """
        # Mock the response from requests.get
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": [{"id": 123, "title": "Test Movie"}]}
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        client = TMDBClient()
        response_data = client._make_request("movie/popular")

        # We expect the call to include the 'api_key' in params
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("api_key", kwargs["params"])
        self.assertEqual(kwargs["params"]["api_key"], "fake_api_key")
        self.assertEqual(response_data, {"results": [{"id": 123, "title": "Test Movie"}]})
    @patch.dict(os.environ, {"TMDB_API_KEY": "fake_api_key"}, clear=True)
    @patch("requests.get")
    def test_get_popular_movies(self, mock_get):
        """
        Tests get_popular_movies() to ensure it calls the correct endpoint.
        """
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"results": []}
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        client = TMDBClient()
        movies = client.get_popular_movies(page=2)
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn("params", kwargs)
        self.assertEqual(kwargs["params"]["page"], 2)
        self.assertEqual(movies, {"results": []})
    @patch.dict(os.environ, {"TMDB_API_KEY": "fake_api_key"}, clear=True)
    @patch("requests.get")
    @patch.object(TMDBClient, "get_collection_movies")
    @patch.object(TMDBClient, "keyword_search")
    def test_search_movies(self, mock_get_collection, mock_get_keyword, mock_get):
        """
        Test that search() aggregates results from collection, keyword, and title search,
        and removes duplicates based on 'id'.
        """
        # 1. Mock collection search
        mock_get_collection.return_value = {"results": [{"id": 1, "title": "Collection Movie"}]}
        # 2. Mock keyword search
        mock_get_keyword.return_value = {"results": [{"id": 2, "title": "Keyword Movie 1"}]}
        # 3. Mock title search
        title_response = {"results": [{"id": 1, "title": "Collection Movie"}, {"id": 4, "title": "Matrix"}]}

        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: title_response)           # search/movie
        ]

        client = TMDBClient()
        result = client.search(query="Matrix", search_type="movie", page=1)
        # Checks that results are correctly added and de-duplicated (Overlapping "id: 1" in collection search and title search)
        expected_titles = {"Collection Movie", "Keyword Movie 1", "Matrix"}
        returned_titles = {item["title"] for item in result["results"]}
        self.assertEqual(returned_titles, expected_titles)
        self.assertEqual(result["query"], "Matrix")
        # Confirm requests.get was called 1 time (title search)
        self.assertEqual(mock_get.call_count, 1)
    def test_get_provider_url(self):
        """
        Tests get_provider_url for both a known provider and an unknown provider.
        """
        client = TMDBClient()
        url_known = client.get_provider_url("Netflix", "My Movie")
        url_unknown = client.get_provider_url("Unknown Service", "My Movie")

        # Netflix uses the search URL pattern "https://www.netflix.com/search?q={title}"
        self.assertIn("https://www.netflix.com/search?q=My+Movie", url_known)
        # If provider not found in PROVIDER_URLS, returns empty string
        self.assertEqual(url_unknown, "")
    @patch.dict(os.environ, {"TMDB_API_KEY": "fake_api_key"}, clear=True)
    @patch("requests.get")
    def test_process_content_item(self, mock_get):
        """
        Tests process_content_item to ensure it calls the right sub-methods 
        and returns a properly structured dict.
        """
        # Mock both get_content_details and get_watch_providers in a single get side_effect
        def side_effect(url, headers=None, params=None):
            if "watch/providers" in url:
                return MagicMock(
                    status_code=200,
                    json=lambda: {
                        "results": {
                            "NO": {
                                "flatrate": [
                                    {"provider_name": "Netflix", "logo_path": "/new_logo.png"}
                                ]
                            }
                        }
                    },
                )
            else:
                # This would be get_content_details
                return MagicMock(
                    status_code=200,
                    json=lambda: {"vote_average": 8.5, "vote_count": 1000},
                )

        mock_get.side_effect = side_effect

        client = TMDBClient()
        dummy_item = {
            "id": 123,
            "title": "Sample Movie",
            "poster_path": "/poster.jpg",
            "media_type": "movie",
            "overview": "A test overview",
            "popularity": 99,
        }
        processed = client.process_content_item(dummy_item, region="NO")

        # Check that the returned dictionary has the expected structure
        self.assertEqual(processed["title"], "Sample Movie")
        self.assertIn("streaming_providers", processed)
        self.assertTrue(processed["streaming_providers"]["available"])
        self.assertEqual(processed["streaming_providers"]["flatrate"][0]["provider_name"], "Netflix")
class AuthTests(TestCase):
    def setUp(self):
        """
        Prepare the test environment by creating:
        1) A Site object with id=1 meeting allauth's requirement for 'testserver'.
        2) A SocialApp for the 'google' provider, linked to the test Site.
        3) A test user in the database for login tests.
        """
        self.site, _ = Site.objects.update_or_create(
            id=1,
            defaults={
                "domain": "testserver",
                "name": "testserver"
            }
        )
        self.social_app = SocialApp.objects.create(
            provider='google',
            name='GoogleTestApp',
            client_id='fake_client_id',
            secret='fake_secret'
        )
        self.social_app.sites.add(self.site)
        self.user = User.objects.create_user(
            username='testlogin',
            password='Secret1234'
        )
    def test_register_success(self):
        """
        Test that posting valid registration data to the 'register' endpoint:
        1) Redirects to 'index' on successful registration.
        2) Actually creates the new user in the database.
        """
        url = reverse('register')
        data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password1': 'SuperSecret123',
            'password2': 'SuperSecret123',
        }
        response = self.client.post(url, data)
        # After a successful registration, you may redirect to index or profile
        self.assertRedirects(response, reverse('index'))
        # Verify user is in database
        user_exists = User.objects.filter(username='testuser').exists()
        self.assertTrue(user_exists)
    def test_login_failure(self):
        """
        Test that posting incorrect credentials at 'login' does not authenticate the user.
        1) The response should return HTTP 200 (re-rendering the form).
        2) The user should remain anonymous (not authenticated).
        3) The 'login.html' template is used.
        """
        url = reverse('login')
        data = {
            'username': 'testlogin',
            'password': 'WrongPassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertTemplateUsed(response, 'login.html')

        
class UserModelTests(TestCase):
    """Tests for User model methods."""
    
    def setUp(self):
        """Create users for testing friend functionality."""
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='Password123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='Password123'
        )
        self.user3 = User.objects.create_user(
            username='testuser3',
            password='Password123'
        )
    
    def test_send_friend_request(self):
        """Test that a user can send a friend request."""
        # Send friend request
        result = self.user1.send_friend_request(self.user2)
        
        # Check result and DB state
        self.assertTrue(result)
        self.assertTrue(FriendRequest.objects.filter(
            from_user=self.user1, 
            to_user=self.user2,
            status='pending'
        ).exists())
    
    def test_send_friend_request_to_self(self):
        """Test that a user cannot send a friend request to themselves."""
        result = self.user1.send_friend_request(self.user1)
        self.assertFalse(result)
        self.assertFalse(FriendRequest.objects.filter(
            from_user=self.user1, 
            to_user=self.user1
        ).exists())
    
    def test_send_duplicate_friend_request(self):
        """Test that duplicate friend requests are prevented."""
        # Create initial request
        self.user1.send_friend_request(self.user2)
        
        # Try to send again
        result = self.user1.send_friend_request(self.user2)
        self.assertFalse(result)
        
        # Check only one request exists
        self.assertEqual(
            FriendRequest.objects.filter(
                from_user=self.user1, 
                to_user=self.user2
            ).count(), 
            1
        )
    
    def test_accept_friend_request(self):
        """Test accepting a friend request."""
        # Create request
        self.user1.send_friend_request(self.user2)
        
        # Accept request
        result = self.user2.accept_friend_request(self.user1)
        
        # Check result and DB state
        self.assertTrue(result)
        self.assertEqual(
            FriendRequest.objects.get(
                from_user=self.user1, 
                to_user=self.user2
            ).status,
            'accepted'
        )
    
    def test_accept_nonexistent_friend_request(self):
        """Test accepting a friend request that doesn't exist."""
        # No request exists yet
        result = self.user2.accept_friend_request(self.user1)
        
        # Should return False
        self.assertFalse(result)
    
    def test_reject_friend_request(self):
        """Test rejecting a friend request."""
        # Create request
        self.user1.send_friend_request(self.user2)
        
        # Reject request
        result = self.user2.reject_friend_request(self.user1)
        
        # Check result and DB state
        self.assertTrue(result)
        self.assertEqual(
            FriendRequest.objects.get(
                from_user=self.user1, 
                to_user=self.user2
            ).status,
            'rejected'
        )
    
    def test_get_friends(self):
        """Test retrieving user's friends."""
        # Create and accept friend requests
        self.user1.send_friend_request(self.user2)
        self.user2.accept_friend_request(self.user1)
        
        self.user3.send_friend_request(self.user1)
        self.user1.accept_friend_request(self.user3)
        
        # Get friends for user1
        friends = self.user1.get_friends()
        
        # Should include user2 and user3
        self.assertEqual(friends.count(), 2)
        self.assertIn(self.user2, friends)
        self.assertIn(self.user3, friends)
    
    def test_unfriend(self):
        """Test removing a friendship."""
        # Create and accept friend request
        self.user1.send_friend_request(self.user2)
        self.user2.accept_friend_request(self.user1)
        
        # Verify they are friends first
        self.assertIn(self.user2, self.user1.get_friends())
        
        # Unfriend
        result = self.user1.unfriend(self.user2)
        
        # Check result and friendship state
        self.assertTrue(result)
        self.assertNotIn(self.user2, self.user1.get_friends())
        self.assertFalse(FriendRequest.objects.filter(
            from_user=self.user1,
            to_user=self.user2
        ).exists())


class WatchedMovieTests(TestCase):
    """Tests for WatchedMovie model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='moviefan',
            password='Password123'
        )
    
    def test_watched_movie_creation(self):
        """Test creating a watched movie entry."""
        movie = WatchedMovie.objects.create(
            user=self.user,
            media_id='12345',
            media_type='movie',
            title='Test Movie',
            poster_path='/test_poster.jpg',
            runtime=120
        )
        
        self.assertEqual(movie.title, 'Test Movie')
        self.assertEqual(movie.media_type, 'movie')
        self.assertEqual(movie.runtime, 120)
        
        # Check it's associated with the user
        self.assertIn(movie, self.user.watched_movies.all())
    
    def test_watched_movie_unique_constraint(self):
        """Test that a user can't have duplicate watched entries for the same content."""
        # Create first entry
        WatchedMovie.objects.create(
            user=self.user,
            media_id='12345',
            media_type='movie',
            title='Test Movie'
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):  # Should raise IntegrityError
            WatchedMovie.objects.create(
                user=self.user,
                media_id='12345',
                media_type='movie',
                title='Test Movie Again'
            )


class BadgeSystemTests(TestCase):
    """Tests for the badge and achievement system."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='achiever',
            password='Password123'
        )
        
        # Create test badges
        self.movie_badge = Badge.objects.create(
            name='Movie Watcher',
            description='Watch 5 movies',
            badge_type='milestone',
            rarity='bronze',
            icon='🎬',
            requirement_count=5,
            requirement_type='movies_watched'
        )
        
        self.review_badge = Badge.objects.create(
            name='Critic',
            description='Write 3 reviews',
            badge_type='critic',
            rarity='silver',
            icon='✍️',
            requirement_count=3,
            requirement_type='reviews_written'
        )
    
    def test_badge_creation(self):
        """Test badge creation and properties."""
        self.assertEqual(self.movie_badge.name, 'Movie Watcher')
        self.assertEqual(self.movie_badge.requirement_count, 5)
        self.assertEqual(self.movie_badge.requirement_type, 'movies_watched')
    
    def test_user_badge_awarding(self):
        """Test awarding a badge to a user."""
        # Create user badge
        user_badge = UserBadge.objects.create(
            user=self.user,
            badge=self.movie_badge
        )
        
        # Check it's properly linked
        self.assertEqual(user_badge.user, self.user)
        self.assertEqual(user_badge.badge, self.movie_badge)
        
        # Check user's badges
        self.assertIn(user_badge, self.user.badges.all())
    
    def test_badge_uniqueness_for_user(self):
        """Test that a user can't be awarded the same badge twice."""
        # Award badge
        UserBadge.objects.create(
            user=self.user,
            badge=self.movie_badge
        )
        
        # Try to award again
        with self.assertRaises(Exception):  # Should raise IntegrityError
            UserBadge.objects.create(
                user=self.user,
                badge=self.movie_badge
            )


class LoginViewTests(TestCase):
    """Extended tests for login functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser',
            password='Password123'
        )
    
    def test_login_success(self):
        """Test successful login redirects to index."""
        url = reverse('login')
        data = {
            'username': 'loginuser',
            'password': 'Password123'
        }
        response = self.client.post(url, data)
        
        # Check redirect and authentication
        self.assertRedirects(response, reverse('index'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_incorrect_password(self):
        """Test login fails with incorrect password."""
        url = reverse('login')
        data = {
            'username': 'loginuser',
            'password': 'WrongPassword'
        }
        response = self.client.post(url, data)
        
        # Should return to login page with error
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertTemplateUsed(response, 'login.html')
    
    def test_login_nonexistent_user(self):
        """Test login fails with nonexistent user."""
        url = reverse('login')
        data = {
            'username': 'nonexistentuser',
            'password': 'Password123'
        }
        response = self.client.post(url, data)
        
        # Should return to login page with error
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertTemplateUsed(response, 'login.html')


class WatchlistTests(TestCase):
    """Tests for watchlist functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='watchlistuser',
            password='Password123'
        )
        self.client.login(username='watchlistuser', password='Password123')
        
        # Add a test item to watchlist
        self.watchlist_item = WatchlistItem.objects.create(
            user=self.user,
            title='Test Movie',
            media_id='12345',
            media_type='movie',
            poster_path='/test_poster.jpg'
        )
    
    def test_watchlist_view(self):
        """Test watchlist view shows user's watchlist items."""
        response = self.client.get(reverse('watchlist'))
        
        # Check response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'watchlist.html')
        
        # Check context
        self.assertIn('watchlist', response.context)
        self.assertEqual(response.context['watchlist'].count(), 1)
        self.assertEqual(response.context['watchlist'][0], self.watchlist_item)
    
    def test_watchlist_requires_login(self):
        """Test that watchlist view requires login."""
        # Logout first
        self.client.logout()
        
        # Try to access watchlist
        response = self.client.get(reverse('watchlist'))
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/?next=/watchlist/')

# Mock classes for testing data extraction/processing
class MockProvider:
    def __init__(self, tmdb_id, name, logo_path):
        self.tmdb_id = tmdb_id
        self.name = name
        self.logo_path = logo_path

class MockProviderInfo:
    def __init__(self, provider, type):
        self.provider = provider
        self.type = type # 'flatrate', 'rent', 'buy'


class MockContentItem: # Simulates Movie or TVShow model instance
    """Unified mock item for testing PopularView and Utility functions."""
    def __init__(self, tmdb_id=1, title="Test Title", overview="Overview", poster_path=None,
                 popularity=50.0, rating=7.5, vote_count=100, release_date=None, first_air_date=None,
                 providers_list=None): # Accepts providers_list, NO media_type here
        self.tmdb_id = tmdb_id
        self.title = title
        self.overview = overview or f"Overview for {title}" # Add default overview
        self.poster_path = poster_path or f"/poster_{tmdb_id}.jpg" # Add default poster
        self.popularity = popularity
        self.rating = rating
        self.vote_count = vote_count
        self.release_date = release_date
        self.first_air_date = first_air_date
        # This attribute is expected by _extract_providers_for_item due to the Prefetch
        self.providers_list = providers_list if providers_list is not None else []
class UtilityTests(TestCase):
    """Tests for utility functions."""
    
    def test_get_validated_region(self):
        """Test region validation function."""
        from myapp.utils import get_validated_region
        
        # Create mock request with region
        request = HttpRequest()
        request.GET = {'region': 'NO'}
        
        # Test valid region
        region = get_validated_region(request)
        self.assertEqual(region, 'NO')
        
        # Test invalid region falls back to default
        request.GET = {'region': 'INVALID'}
        region = get_validated_region(request)
        self.assertEqual(region, 'US')  # Default in the function
        
        # Test missing region falls back to default
        request.GET = {}
        region = get_validated_region(request)
        self.assertEqual(region, 'US')
    
    def test_get_poster_url(self):
        """Test poster URL formatting."""
        from myapp.utils import get_poster_url
        
        # Test TMDB path
        poster_path = '/test_poster.jpg'
        url = get_poster_url(poster_path)
        self.assertEqual(url, 'https://image.tmdb.org/t/p/w500/test_poster.jpg')
        
        # Test local media path
        poster_path = 'posters/test_poster.jpg'
        url = get_poster_url(poster_path)
        self.assertTrue(url.startswith('/media/posters/test_poster.jpg'))
        
        # Test full URL
        poster_path = 'https://example.com/poster.jpg'
        url = get_poster_url(poster_path)
        self.assertEqual(url, 'https://example.com/poster.jpg')
        
        # Test None
        url = get_poster_url(None)
        self.assertIsNone(url)
    def test_get_provider_logo_url(self):
        """Test provider logo URL construction."""
        base = "https://image.tmdb.org/t/p/w92"
        # Test path starting with /
        self.assertEqual(get_provider_logo_url("/logo1.jpg"), f"{base}/logo1.jpg")
        # Test path not starting with / (should still work by prepending /)
        self.assertEqual(get_provider_logo_url("logo2.jpg"), f"{base}/logo2.jpg")
        # Test None
        self.assertIsNone(get_provider_logo_url(None))
        # Test Empty String
        self.assertIsNone(get_provider_logo_url(""))
        # Test string 'None'
        self.assertIsNone(get_provider_logo_url("None"))

    def test_encode_filters_for_pagination(self):
        """Test encoding of GET parameters, excluding 'page'."""
        # Test empty dict
        self.assertEqual(encode_filters_for_pagination(QueryDict('')), "")
        # Test dict with only page
        self.assertEqual(encode_filters_for_pagination(QueryDict('page=2')), "")
        # Test dict with other params
        q = QueryDict('region=NO&provider=8')
        self.assertEqual(encode_filters_for_pagination(q), "region=NO&provider=8")
        # Test dict with other params and page
        q = QueryDict('region=NO&provider=8&page=3')
        self.assertEqual(encode_filters_for_pagination(q), "region=NO&provider=8")
        # Test dict with list params
        q = QueryDict('provider=8&provider=9&region=US&sort=pop')
        # Note: urlencode order isn't guaranteed, but content should match
        self.assertIn("provider=8", encode_filters_for_pagination(q))
        self.assertIn("provider=9", encode_filters_for_pagination(q))
        self.assertIn("region=US", encode_filters_for_pagination(q))
        self.assertIn("sort=pop", encode_filters_for_pagination(q))
        self.assertNotIn("page=", encode_filters_for_pagination(q))

    def test_paginate_results(self):
        """Test pagination logic including edge cases."""
        items = list(range(30)) # 0 to 29
        items_per_page = 10

        # Test valid page
        page_obj_valid = paginate_results(items, 2, items_per_page)
        self.assertIsInstance(page_obj_valid, Page)
        self.assertEqual(page_obj_valid.number, 2)
        self.assertEqual(list(page_obj_valid.object_list), list(range(10, 20)))

        # Test PageNotAnInteger (invalid string) -> defaults to page 1
        page_obj_invalid_str = paginate_results(items, 'abc', items_per_page)
        self.assertEqual(page_obj_invalid_str.number, 1)
        self.assertEqual(list(page_obj_invalid_str.object_list), list(range(0, 10)))

        # Test PageNotAnInteger (None case simulation - view passes 1)
        page_obj_default = paginate_results(items, 1, items_per_page)
        self.assertEqual(page_obj_default.number, 1) # <<< Assert immediately after the call

        # Test EmptyPage (page > num_pages) -> defaults to last page
        page_obj_empty_high = paginate_results(items, 5, items_per_page) # Only 3 pages
        self.assertEqual(page_obj_empty_high.number, 3) # <<< Assert immediately after the call
        self.assertEqual(list(page_obj_empty_high.object_list), list(range(20, 30)))

        # Test EmptyPage (page < 1) -> Paginator handles this, defaults to page 1
        page_obj_empty_low = paginate_results(items, 0, items_per_page)
        self.assertEqual(page_obj_empty_low.number, 3)

    # Test the private helper, mocking its dependency
    @patch('myapp.utils.get_provider_logo_url', return_value="http://mocklogo.url/img.jpg")
    def test_extract_providers_for_item(self, mock_get_logo):
        """Test extraction and formatting of provider info from a mock item."""
        # Arrange: Setup mock providers
        provider_netflix = MockProvider(8, "Netflix", "/netflix.jpg")
        provider_disney = MockProvider(9, "Disney+", "/disney.jpg")
        provider_hbo = MockProvider(15, "HBO Max", "/hbo.jpg")

        provider_info_netflix = MockProviderInfo(provider_netflix, 'flatrate')
        provider_info_disney_rent = MockProviderInfo(provider_disney, 'rent')
        provider_info_hbo_buy = MockProviderInfo(provider_hbo, 'buy')

        # Case 1: Item with multiple providers
        item1 = MockContentItem(providers_list=[provider_info_netflix, provider_info_disney_rent, provider_info_hbo_buy])
        # Case 2: Item with no providers
        item2 = MockContentItem(providers_list=[])
        # Case 3: Item where attribute might be missing (simulate Prefetch fail)
        item3 = MagicMock()
        del item3.providers_list # Ensure attribute doesn't exist

        # Act
        result1 = _extract_providers_for_item(item1)
        result2 = _extract_providers_for_item(item2)
        result3 = _extract_providers_for_item(item3)


        # Assert Case 1
        self.assertTrue(result1['available'])
        self.assertEqual(len(result1['flatrate']), 1)
        self.assertEqual(result1['flatrate'][0]['provider_name'], "Netflix")
        self.assertEqual(result1['flatrate'][0]['logo_path'], "http://mocklogo.url/img.jpg")
        self.assertEqual(result1['flatrate'][0]['provider_id'], 8)
        self.assertEqual(len(result1['rent']), 1)
        self.assertEqual(result1['rent'][0]['provider_name'], "Disney+")
        self.assertEqual(result1['rent'][0]['provider_id'], 9)
        self.assertEqual(len(result1['buy']), 1)
        self.assertEqual(result1['buy'][0]['provider_name'], "HBO Max")
        self.assertEqual(result1['buy'][0]['provider_id'], 15)
        mock_get_logo.assert_has_calls([call("/netflix.jpg"), call("/disney.jpg"), call("/hbo.jpg")])
        self.assertEqual(mock_get_logo.call_count, 3) # Called for each provider

        # Assert Case 2
        self.assertFalse(result2['available'])
        self.assertEqual(result2['flatrate'], [])
        self.assertEqual(result2['rent'], [])
        self.assertEqual(result2['buy'], [])

        # Assert Case 3 (should not crash)
        self.assertFalse(result3['available'])
        self.assertEqual(result3['flatrate'], [])
        self.assertEqual(result3['rent'], [])
        self.assertEqual(result3['buy'], [])

    # Test the main processing function, mocking its dependencies
    @patch('myapp.utils._extract_providers_for_item')
    @patch('myapp.utils.get_poster_url')
    def test_process_content_item(self, mock_get_poster, mock_extract_providers):
        """Test conversion of a mock model item to a template dictionary."""
        # Arrange
        mock_providers_dict = {'flatrate': [{'name':'mock'}], 'rent':[], 'buy':[], 'available': True}
        mock_extract_providers.return_value = mock_providers_dict
        mock_get_poster.return_value = "http://mockposter.url/poster.jpg"

        watchlist = ['101', '202'] # Watchlist contains item 101

        # Case 1: Movie item, in watchlist
        item_movie = MockContentItem(tmdb_id=101, title="Test Movie", popularity=123.45, rating=8.1, vote_count=500, release_date='2023-01-01', poster_path='/movie.jpg')
        # Case 2: TV item, not in watchlist, rating is None
        item_tv = MockContentItem(tmdb_id=303, title="Test Show", popularity=99.0, rating=None, vote_count=50, first_air_date='2022-05-10', poster_path='/tv.jpg')

        # Act
        result_movie = process_content_item(item_movie, watchlist, 'movie')
        result_tv = process_content_item(item_tv, watchlist, 'tv')

        # Assert Movie
        self.assertEqual(result_movie['id'], '101')
        self.assertEqual(result_movie['title'], "Test Movie")
        self.assertEqual(result_movie['popularity'], 123.45)
        self.assertEqual(result_movie['rating'], 8.1)
        self.assertEqual(result_movie['vote_count'], 500)
        self.assertEqual(result_movie['release_date'], '2023-01-01')
        self.assertEqual(result_movie['poster_url'], "http://mockposter.url/poster.jpg")
        self.assertEqual(result_movie['streaming_providers'], mock_providers_dict)
        self.assertTrue(result_movie['in_watchlist'])

        # Assert TV
        self.assertEqual(result_tv['id'], '303')
        self.assertEqual(result_tv['title'], "Test Show")
        self.assertEqual(result_tv['media_type'], 'tv')
        self.assertEqual(result_tv['popularity'], 99.0)
        self.assertEqual(result_tv['rating'], 0.0) # Check default for None rating
        self.assertEqual(result_tv['vote_count'], 50)
        self.assertEqual(result_tv['release_date'], '2022-05-10') # Check it gets first_air_date
        self.assertEqual(result_tv['poster_url'], "http://mockposter.url/poster.jpg")
        self.assertEqual(result_tv['streaming_providers'], mock_providers_dict)
        self.assertFalse(result_tv['in_watchlist'])
        mock_extract_providers.assert_called_with(item_tv)
        mock_get_poster.assert_called_with('/tv.jpg')
# Mock constants if they aren't easily importable or for isolation
INITIAL_FETCH_LIMIT = 50 # Example value
ITEMS_PER_PAGE = 15
# Dummy provider data for mocking get_providers_for_region_filter
class MockStreamingProvider:
    def __init__(self, tmdb_id, name, logo_path):
        self.tmdb_id = tmdb_id
        self.name = name
        self.logo_path = logo_path

DUMMY_PROVIDERS = [
    MockStreamingProvider(8, 'Netflix', '/netflix.jpg'),
    MockStreamingProvider(9, 'Disney+', '/disney.jpg'),
    MockStreamingProvider(15, 'Hulu', '/hulu.jpg'),
]
# --- Test Class ---
class PopularViewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create a user that can be used across tests if needed
        User = get_user_model()
        cls.test_user = User.objects.create_user(username='testuser', password='password123')

    def setUp(self):
        self.client = Client()
        self.popular_url = reverse('popular')

        # --- Common Mock Setup for Pagination ---
        mock_paginator = MagicMock(spec=Paginator)
        mock_paginator.num_pages = 1
        self.mock_empty_page = MagicMock(spec=Page)
        self.mock_empty_page.object_list = []
        self.mock_empty_page.__iter__ = lambda s: iter([])
        self.mock_empty_page.has_other_pages = MagicMock(return_value=False)
        self.mock_empty_page.has_previous = MagicMock(return_value=False)
        self.mock_empty_page.has_next = MagicMock(return_value=False)
        self.mock_empty_page.number = 1
        self.mock_empty_page.paginator = mock_paginator


    # --- Test 1: Basic Load (Existing) ---
    @patch('myapp.views.get_validated_region', return_value='XX')
    @patch('myapp.views.get_watchlist_ids', return_value=[])
    @patch('myapp.views.get_popular_movies', return_value=[])
    @patch('myapp.views.get_popular_tv_shows', return_value=[])
    @patch('myapp.views.process_content_item')
    @patch('myapp.views.paginate_results')
    @patch('myapp.views.get_providers_for_region_filter', return_value=[])
    @patch('myapp.views.encode_filters_for_pagination', return_value='')
    @patch('myapp.views.get_provider_logo_url')
    def test_popular_view_loads_ok_and_uses_correct_template(
        self, mock_get_logo, mock_encode_filters, mock_get_providers, mock_paginate,
        mock_process, mock_get_tv, mock_get_movies, mock_get_watchlist, mock_get_region):
        # Arrange
        mock_paginate.return_value = self.mock_empty_page
        # Act
        response = self.client.get(self.popular_url)
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'popular.html')
        mock_get_region.assert_called_once()
        mock_get_movies.assert_called_once()
        mock_get_tv.assert_called_once()
        mock_paginate.assert_called_once()
        mock_get_providers.assert_called_once()
        mock_encode_filters.assert_called_once()

    # --- Test 2: Check Region Parameter Usage (Existing) ---
    @patch('myapp.views.get_validated_region', return_value='GB')
    @patch('myapp.views.get_watchlist_ids', return_value=[])
    @patch('myapp.views.get_popular_movies', return_value=[])
    @patch('myapp.views.get_popular_tv_shows', return_value=[])
    @patch('myapp.views.process_content_item')
    @patch('myapp.views.paginate_results')
    @patch('myapp.views.get_providers_for_region_filter', return_value=[])
    @patch('myapp.views.encode_filters_for_pagination', return_value='region=GB')
    @patch('myapp.views.get_provider_logo_url')
    def test_popular_view_uses_region_parameter_for_fetching(
        self, mock_get_logo, mock_encode_filters, mock_get_providers, mock_paginate,
        mock_process, mock_get_tv, mock_get_movies, mock_get_watchlist, mock_get_region):
        # Arrange
        mock_paginate.return_value = self.mock_empty_page
        url_with_region = f"{self.popular_url}?region=GB"
        # Act
        response = self.client.get(url_with_region)
        # Assert
        self.assertEqual(response.status_code, 200)
        mock_get_movies.assert_called_once_with('GB', ANY, ANY)
        mock_get_tv.assert_called_once_with('GB', ANY, ANY)
        mock_get_providers.assert_called_once_with('GB')
        self.assertEqual(response.context.get('selected_region'), 'GB')

    # --- Test 3: Check Essential Context Variables (Existing) ---
    @patch('myapp.views.get_validated_region', return_value='US')
    @patch('myapp.views.get_watchlist_ids', return_value=[])
    @patch('myapp.views.get_popular_movies', return_value=[])
    @patch('myapp.views.get_popular_tv_shows', return_value=[])
    @patch('myapp.views.process_content_item')
    @patch('myapp.views.paginate_results')
    @patch('myapp.views.get_providers_for_region_filter', return_value=[])
    @patch('myapp.views.encode_filters_for_pagination', return_value='')
    @patch('myapp.views.get_provider_logo_url')
    def test_popular_view_context_has_required_keys(
        self, mock_get_logo, mock_encode_filters, mock_get_providers, mock_paginate,
        mock_process, mock_get_tv, mock_get_movies, mock_get_watchlist, mock_get_region):
        # Arrange
        mock_paginate.return_value = self.mock_empty_page
        # Act
        response = self.client.get(self.popular_url)
        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertIn('page_obj', response.context)
        self.assertIsNotNone(response.context['page_obj'])
        self.assertTrue(hasattr(response.context['page_obj'], 'paginator'))
        self.assertEqual(response.context['page_obj'].paginator.num_pages, 1)
        self.assertIn('selected_region', response.context)
        self.assertEqual(response.context['selected_region'], 'US')
        self.assertIn('REGION_CHOICES', response.context)
        self.assertEqual(response.context['REGION_CHOICES'], REGION_CHOICES) # Uses imported or fallback
        self.assertIn('watchlist_ids', response.context)
        self.assertEqual(response.context['watchlist_ids'], [])
        self.assertIn('all_providers', response.context)
        self.assertEqual(response.context['all_providers'], [])
        self.assertIn('selected_provider_ids', response.context)
        self.assertEqual(response.context['selected_provider_ids'], [])
        self.assertIn('current_filters_encoded', response.context)
        self.assertEqual(response.context['current_filters_encoded'], '')
        self.assertIn('MEDIA_URL', response.context)
        self.assertEqual(response.context['MEDIA_URL'], settings.MEDIA_URL)

    # --- Test 4: Provider Filter Parsing and Usage (NEW) ---
    @patch('myapp.views.get_validated_region', return_value='US')
    @patch('myapp.views.get_watchlist_ids', return_value=[])
    @patch('myapp.views.get_popular_movies', return_value=[]) # Doesn't matter what they return here
    @patch('myapp.views.get_popular_tv_shows', return_value=[])
    @patch('myapp.views.process_content_item')
    @patch('myapp.views.paginate_results')
    @patch('myapp.views.get_providers_for_region_filter', return_value=DUMMY_PROVIDERS) # Return providers
    @patch('myapp.views.encode_filters_for_pagination', return_value='provider=8&provider=15')
    @patch('myapp.views.get_provider_logo_url', return_value='http://example.com/logo.jpg') # Mock logo URL call
    def test_popular_view_uses_provider_filter(
        self, mock_get_logo, mock_encode_filters, mock_get_providers, mock_paginate,
        mock_process, mock_get_tv, mock_get_movies, mock_get_watchlist, mock_get_region):
        """
        Verifies provider IDs from GET params are parsed and passed to data fetching
        and included in the context. Also checks provider logos are processed.
        """
        # Arrange
        mock_paginate.return_value = self.mock_empty_page
        # Pass valid numeric IDs and an invalid one to test parsing
        url = f"{self.popular_url}?provider=8&provider=invalid&provider=15"
        expected_provider_ids = [8, 15] # Only valid integers should be kept

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, 200)

        # Verify the *parsed* valid provider IDs were used for data fetching
        mock_get_movies.assert_called_once_with('US', ANY, expected_provider_ids)
        mock_get_tv.assert_called_once_with('US', ANY, expected_provider_ids)

        # Verify context contains the parsed IDs and the list of available providers
        self.assertEqual(response.context.get('selected_provider_ids'), expected_provider_ids)
        self.assertEqual(len(response.context.get('all_providers')), len(DUMMY_PROVIDERS))
        self.assertIn('all_providers', response.context)

        # Verify the function to get logo URLs was called for each available provider
        mock_get_providers.assert_called_once_with('US') # Ensure providers were fetched
        self.assertEqual(mock_get_logo.call_count, len(DUMMY_PROVIDERS))


    # --- Test 5: Authenticated User Watchlist Check (NEW) ---
    @patch('myapp.views.get_validated_region', return_value='CA')
    @patch('myapp.views.get_watchlist_ids') # Mock the function directly
    @patch('myapp.views.get_popular_movies', return_value=[])
    @patch('myapp.views.get_popular_tv_shows', return_value=[])
    @patch('myapp.views.process_content_item')
    @patch('myapp.views.paginate_results')
    @patch('myapp.views.get_providers_for_region_filter', return_value=[])
    @patch('myapp.views.encode_filters_for_pagination', return_value='')
    @patch('myapp.views.get_provider_logo_url')
    def test_popular_view_gets_watchlist_for_logged_in_user(
        self, mock_get_logo, mock_encode_filters, mock_get_providers, mock_paginate,
        mock_process, mock_get_tv, mock_get_movies, mock_get_watchlist, mock_get_region):
        """
        Verifies get_watchlist_ids is called and its result put in context for authenticated users.
        """
        # Arrange
        mock_paginate.return_value = self.mock_empty_page
        expected_watchlist = ['movie-123', 'tv-456']
        mock_get_watchlist.return_value = expected_watchlist # Setup mock return value

        # Log in the test user created in setUpTestData
        self.client.force_login(self.test_user)

        # Act
        response = self.client.get(self.popular_url)

        # Assert
        self.assertEqual(response.status_code, 200)

        # Check get_watchlist_ids was called, potentially with the user object
        # Using ANY here is safer if the exact arguments might change slightly
        mock_get_watchlist.assert_called_once_with(self.test_user)

        # Check the returned watchlist is in the context
        self.assertEqual(response.context.get('watchlist_ids'), expected_watchlist)


    # --- Test 6: Pagination Parameter Usage (NEW) ---
    @patch('myapp.views.get_validated_region', return_value='US')
    @patch('myapp.views.get_watchlist_ids', return_value=[])
    @patch('myapp.views.get_popular_movies', return_value=[])
    @patch('myapp.views.get_popular_tv_shows', return_value=[])
    @patch('myapp.views.process_content_item')
    @patch('myapp.views.paginate_results') # Mock the function we want to check args for
    @patch('myapp.views.get_providers_for_region_filter', return_value=[])
    @patch('myapp.views.encode_filters_for_pagination', return_value='page=3')
    @patch('myapp.views.get_provider_logo_url')
    def test_popular_view_uses_page_parameter(
        self, mock_get_logo, mock_encode_filters, mock_get_providers, mock_paginate,
        mock_process, mock_get_tv, mock_get_movies, mock_get_watchlist, mock_get_region):
        """
        Verifies the 'page' GET parameter is correctly passed to paginate_results.
        """
        # Arrange
        mock_paginate.return_value = self.mock_empty_page
        requested_page_number = '3' # request.GET gives strings
        url = f"{self.popular_url}?page={requested_page_number}"

        # Act
        response = self.client.get(url)

        # Assert
        self.assertEqual(response.status_code, 200)

        # Check that paginate_results was called with the correct page number
        # The first argument is the list of items (which is empty here after sorting),
        # the second is the page number, the third is ITEMS_PER_PAGE
        mock_paginate.assert_called_once_with(ANY, requested_page_number, ITEMS_PER_PAGE)

    # --- Test 7: Data Processing and Sorting Verification (NEW) ---
    @patch('myapp.views.get_validated_region', return_value='US')
    @patch('myapp.views.get_watchlist_ids', return_value=[])
    @patch('myapp.views.get_popular_movies') # Mocked below
    @patch('myapp.views.get_popular_tv_shows') # Mocked below
    @patch('myapp.views.process_content_item') # Mocked below
    @patch('myapp.views.paginate_results') # Check args passed to this
    @patch('myapp.views.get_providers_for_region_filter', return_value=[])
    @patch('myapp.views.encode_filters_for_pagination', return_value='')
    @patch('myapp.views.get_provider_logo_url')
    def test_popular_view_processes_and_sorts_data(
        self, mock_get_logo, mock_encode_filters, mock_get_providers, mock_paginate,
        mock_process, mock_get_tv, mock_get_movies, mock_get_watchlist, mock_get_region):
        """
        Verifies items are fetched, processed, sorted by popularity/rating,
        and then passed to pagination.
        """
        # Arrange: Mock fetched items (unsorted)
        # --- REMOVE media_type='...' from these lines ---
        movie1 = MockContentItem(tmdb_id=101, title="LowPop Movie", popularity=10.0, rating=8.0)
        movie2 = MockContentItem(tmdb_id=102, title="HighPop Movie", popularity=100.0, rating=7.0)
        tv1 = MockContentItem(tmdb_id=201, title="MidPop TV", popularity=50.0, rating=9.0)
        tv2 = MockContentItem(tmdb_id=202, title="HighPop TV LowRating", popularity=100.0, rating=6.0)

        mock_get_movies.return_value = [movie1, movie2]
        mock_get_tv.return_value = [tv1, tv2]

        # Mock process_content_item to just return a dict with key info
        def simple_process(item, watchlist_ids, media_type):
            return {
                'id': item.tmdb_id,
                'title': item.title,
                'popularity': item.popularity,
                'rating': item.rating,
                'media_type': media_type, # Use the arg passed by the view
            }
        mock_process.side_effect = simple_process

        # This is what we expect process_content_item to return
        processed_movie1 = simple_process(movie1, [], 'movie')
        processed_movie2 = simple_process(movie2, [], 'movie')
        processed_tv1 = simple_process(tv1, [], 'tv')
        processed_tv2 = simple_process(tv2, [], 'tv')

        # This is the order they should be in *after* sorting in the view
        expected_sorted_list = [
            processed_movie2, # pop 100, rating 7
            processed_tv2,    # pop 100, rating 6 (lower rating than movie2)
            processed_tv1,    # pop 50, rating 9
            processed_movie1, # pop 10, rating 8
        ]

        mock_paginate.return_value = self.mock_empty_page # We only care about args passed to it

        # Act
        response = self.client.get(self.popular_url)

        # Assert
        self.assertEqual(response.status_code, 200)

        # Check process_content_item was called for each item
        mock_process.assert_has_calls([
            call(movie1, [], 'movie'),
            call(movie2, [], 'movie'),
            call(tv1, [], 'tv'),
            call(tv2, [], 'tv'),
        ], any_order=True) # Order doesn't matter here
        self.assertEqual(mock_process.call_count, 4)

        # Check that paginate_results was called with the *correctly sorted* list
        mock_paginate.assert_called_once()
        call_args, call_kwargs = mock_paginate.call_args
        actual_list_passed_to_paginate = call_args[0]
        self.assertEqual(actual_list_passed_to_paginate, expected_sorted_list)


    # --- Test 8: Error Handling during Data Fetching ---
    @patch('myapp.views.get_validated_region', return_value='DE')
    @patch('myapp.views.get_watchlist_ids', return_value=[])
    @patch('myapp.views.get_popular_movies') # This will raise the error
    @patch('myapp.views.get_popular_tv_shows') # Won't be called if movies errors
    @patch('myapp.views.process_content_item') # Won't be called
    @patch('myapp.views.paginate_results') # Won't be called
    @patch('myapp.views.get_providers_for_region_filter') # Should be called in except block
    @patch('myapp.views.encode_filters_for_pagination') # Should be called in except block
    @patch('myapp.views.get_provider_logo_url')
    def test_popular_view_handles_exception_gracefully(
        self, mock_get_logo, mock_encode_filters, mock_get_providers, mock_paginate,
        mock_process, mock_get_tv, mock_get_movies, mock_get_watchlist, mock_get_region):
        """
        Verifies the view catches exceptions during data fetching, returns 200,
        and sets an error message in the context.
        """
        # Arrange
        error_message = "Database connection failed"
        mock_get_movies.side_effect = Exception(error_message)
        mock_get_providers.return_value = DUMMY_PROVIDERS # Mock providers fetch
        mock_encode_filters.return_value = "region=DE"
        url_with_filters = f"{self.popular_url}?region=DE&provider=8"

        # Act
        response = self.client.get(url_with_filters)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'popular.html')
        self.assertIn('error', response.context)
        self.assertIsNotNone(response.context['error'])
        self.assertIn('unexpected error', response.context['error'])
        self.assertIsNone(response.context.get('page_obj'))
        mock_get_tv.assert_not_called()
        mock_process.assert_not_called()
        mock_paginate.assert_not_called()
        mock_get_providers.assert_called_once_with('DE')
        mock_encode_filters.assert_called_once()
        mock_get_logo.assert_not_called()

        self.assertEqual(response.context.get('selected_region'), 'DE')
        # Check the raw mocked providers list is in the context
        self.assertEqual(response.context.get('all_providers'), DUMMY_PROVIDERS)
        self.assertEqual(response.context.get('selected_provider_ids'), [8])
        self.assertEqual(response.context.get('current_filters_encoded'), "region=DE")


    # --- Test 9: Handling of Empty Movie/TV Results (NEW) ---
    @patch('myapp.views.get_validated_region', return_value='FR')
    @patch('myapp.views.get_watchlist_ids', return_value=[])
    @patch('myapp.views.get_popular_movies', return_value=[]) # Explicitly return empty
    @patch('myapp.views.get_popular_tv_shows', return_value=[]) # Explicitly return empty
    @patch('myapp.views.process_content_item') # Should NOT be called
    @patch('myapp.views.paginate_results') # Should be called with empty list
    @patch('myapp.views.get_providers_for_region_filter', return_value=[])
    @patch('myapp.views.encode_filters_for_pagination', return_value='')
    @patch('myapp.views.get_provider_logo_url')
    def test_popular_view_handles_no_content_found(
        self, mock_get_logo, mock_encode_filters, mock_get_providers, mock_paginate,
        mock_process, mock_get_tv, mock_get_movies, mock_get_watchlist, mock_get_region):
        """
        Verifies behavior when no popular movies or TV shows are found for the region/filters.
        """
        # Arrange
        mock_paginate.return_value = self.mock_empty_page # Simulate pagination of empty list

        # Act
        response = self.client.get(self.popular_url)

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'popular.html')

        # Check main data fetching functions were called
        mock_get_movies.assert_called_once()
        mock_get_tv.assert_called_once()

        # Crucially, check processing was NOT called as there was nothing to process
        mock_process.assert_not_called()

        # Check pagination was called with an empty list after sorting
        mock_paginate.assert_called_once_with([], ANY, ANY) # Page number and items_per_page don't matter much here

        # Check the final page object in context is empty
        self.assertIn('page_obj', response.context)
        self.assertEqual(list(response.context['page_obj']), []) # Iterate the mock page obj
        self.assertEqual(response.context['page_obj'].object_list, [])