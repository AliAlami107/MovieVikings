"""
Django views for the MovieVikings application.

This module contains all view functions that handle HTTP requests and responses,
including content display, user management, and social features.
"""

from django.shortcuts import render, redirect
from .tmdb_client import TMDBClient
import random
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .models import User, WatchlistItem, WatchedMovie, FriendRequest
from django.core.paginator import Paginator, EmptyPage
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from django.http import Http404
from myapp.models import StreamingService, REGION_CHOICES
from django.conf import settings
from .utils import (get_validated_region, get_popular_movies, get_popular_tv_shows,paginate_results,
                    process_content_item, get_providers_for_region_filter, encode_filters_for_pagination,
                    get_provider_logo_url)
from django.db import models
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from urllib.parse import unquote


# Create your views here.
def index(request):
    """
    Render the homepage of the application.
    
    Returns:
        HttpResponse: Rendered index.html template
    """
    return render(request, 'index.html')

def get_watchlist_ids(user):
    """
    Helper function to get all media IDs in user's watchlist.
    
    Args:
        user: The user object to get watchlist IDs for
        
    Returns:
        list: List of media IDs as strings, or empty list if user is not authenticated
    """
    if user.is_authenticated:
        # Convert IDs to strings to match with template comparisons
        return [str(id) for id in WatchlistItem.objects.filter(user=user).values_list('media_id', flat=True)]
    return []

def search(request):
    """
    Handle search requests for movies and TV shows.
    
    Searches TMDB API based on user query and returns matching results.
    Results are filtered by region and include streaming availability information.
    
    Args:
        request: HTTP request object containing search query and region
        
    Returns:
        HttpResponse: Rendered template with search results
    """
    query = request.GET.get('query', '')
    region = request.GET.get('region', 'NO')
    search_results = []
    watchlist_ids = get_watchlist_ids(request.user)
    
    if query:
        try:
            tmdb = TMDBClient()
            response = tmdb.search(query=query, search_type='multi')
            
            for item in response.get('results', []):
                if item.get('media_type') in ['movie', 'tv']:
                    result = tmdb.process_content_item(item, region)
                    # Convert ID to string for comparison
                    result['id'] = str(result['id'])
                    search_results.append(result)
                    
        except Exception as e:
            print(f"Error searching TMDB: {e}")
    
    return render(request, 'index.html', {
        'search_results': search_results,
        'query': query,
        'selected_region': region,
        'watchlist_ids': watchlist_ids
    })

def randomizer(request):
    """
    Render the randomizer page for discovering random content.
    
    Returns:
        HttpResponse: Rendered randomizer.html template
    """
    return render(request, 'randomizer.html')

def get_random_content(request):
    """
    Get random content for the content wheel feature.
    
    Fetches a mix of movies and TV shows based on selected genres and region.
    Ensures an even distribution of content types and includes streaming availability.
    
    Args:
        request: HTTP request object containing genre and region filters
        
    Returns:
        JsonResponse: JSON containing processed content items and genre list
    """
    try:
        region = request.GET.get('region', 'NO')  # Default to Norway
        genres = request.GET.getlist('genre', [])  # Get selected genres
        tmdb = TMDBClient()
        
        # Initialize empty lists for content
        all_content = []
        
        # If specific genres are selected and it's not the "all" option
        if genres and 'all' not in genres:
            # Get content by genre
            for genre_id in genres:
                # Make sure genre_id is a valid integer
                try:
                    genre_id = int(genre_id)
                    # Get movies with this genre (fetch 2 pages for more variety)
                    for page in range(1, 3):
                        movies = tmdb.discover_by_genre('movie', genre_id, page)['results']
                        for item in movies:
                            item['media_type'] = 'movie'
                            all_content.append(item)
                    
                    # Get TV shows with this genre (fetch 2 pages for more variety)
                    for page in range(1, 3):
                        tv_shows = tmdb.discover_by_genre('tv', genre_id, page)['results']
                        for item in tv_shows:
                            item['media_type'] = 'tv'
                            all_content.append(item)
                except (ValueError, TypeError):
                    pass  # Skip invalid genre IDs
        else:
            # Get broader selection of movies and TV shows (3 pages each for more variety)
            for page in range(1, 4):
                movies = tmdb.get_popular_movies(page=page)['results']
                for item in movies:
                    item['media_type'] = 'movie'
                    all_content.append(item)
                
                tv_shows = tmdb.get_popular_tv_shows(page=page)['results']
                for item in tv_shows:
                    item['media_type'] = 'tv'
                    all_content.append(item)
                
                # Add trending content for even more variety
                if page == 1:  # Only need to do this once
                    trending_movies = tmdb.get_trending_movies()['results']
                    for item in trending_movies:
                        item['media_type'] = 'movie'
                        all_content.append(item)
                    
                    trending_tv = tmdb.get_trending_tv_shows()['results']
                    for item in trending_tv:
                        item['media_type'] = 'tv'
                        all_content.append(item)
        
        # Remove duplicates by ID
        seen_ids = set()
        unique_content = []
        for item in all_content:
            if item['id'] not in seen_ids:
                seen_ids.add(item['id'])
                unique_content.append(item)
        
        # Shuffle all content
        random.shuffle(unique_content)
        
        # Select and process items (ensure we have exactly 12 items for the wheel)
        selected_content = []
        movie_count = 0
        tv_count = 0
        
        # First pass: try to get an even mix of movies and TV shows
        for item in unique_content:
            if len(selected_content) >= 12:
                break
            
            if item['media_type'] == 'movie' and movie_count < 6:
                if item.get('poster_path'):  # Only include items with posters
                    selected_content.append(item)
                    movie_count += 1
            elif item['media_type'] == 'tv' and tv_count < 6:
                if item.get('poster_path'):  # Only include items with posters
                    selected_content.append(item)
                    tv_count += 1
        
        # Second pass: if we don't have enough items, fill with any type
        if len(selected_content) < 12:
            for item in unique_content:
                if item not in selected_content and item.get('poster_path'):
                    selected_content.append(item)
                    if len(selected_content) >= 12:
                        break
        
        # Process results with streaming info
        processed_results = []
        for item in selected_content:
            result = tmdb.process_content_item(item, region)
            processed_results.append(result)
        
        # Get the list of genres for the UI
        genre_list = []
        try:
            movie_genres = tmdb.get_genre_list('movie').get('genres', [])
            tv_genres = tmdb.get_genre_list('tv').get('genres', [])
            
            # Combine genres from both movie and TV, avoiding duplicates
            seen_genre_ids = set()
            for genre in movie_genres + tv_genres:
                if genre['id'] not in seen_genre_ids:
                    seen_genre_ids.add(genre['id'])
                    genre_list.append(genre)
            
            # Sort by name
            genre_list.sort(key=lambda x: x['name'])
        except Exception as e:
            print(f"Error fetching genre list: {e}")
        
        return JsonResponse({
            'results': processed_results,
            'genres': genre_list
        })
    except Exception as e:
        print(f"Error in get_random_content: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

ITEMS_PER_PAGE = 15
INITIAL_FETCH_LIMIT = 3000
def popular(request):
    """
    Display globally popular movies and TV shows with pagination and filters.
    
    Fetches popular content from TMDB API, applies region and provider filters,
    and displays results in a paginated format.
    
    Args:
        request: HTTP request object containing filter parameters
        
    Returns:
        HttpResponse: Rendered template with paginated results
    """
    try:
        # --- Get Parameters ---
        selected_region = get_validated_region(request)
        page_number = request.GET.get('page', 1)
        # Get and validate selected provider ID
        selected_provider_ids_str = request.GET.getlist('provider')
        selected_provider_ids = []
        if selected_provider_ids_str:
            for pid_str in selected_provider_ids_str:
                if pid_str.isdigit():
                    selected_provider_ids.append(int(pid_str))

        watchlist_ids = get_watchlist_ids(request.user) if request.user.is_authenticated else []

        # --- Fetch Data (Pass provider filter to utils) ---
        movies_qs = get_popular_movies(selected_region, INITIAL_FETCH_LIMIT, selected_provider_ids)
        tv_shows_qs = get_popular_tv_shows(selected_region, INITIAL_FETCH_LIMIT, selected_provider_ids)

        # --- Process Data ---
        all_content_dicts = [
            process_content_item(item, watchlist_ids, 'movie') for item in movies_qs
        ]
        all_content_dicts.extend([
            process_content_item(item, watchlist_ids, 'tv') for item in tv_shows_qs
        ])

        # --- Sort Combined List ---
        all_content_dicts.sort(key=lambda x: (x.get('popularity', 0), x.get('rating', 0)), reverse=True)

        # --- Paginate Results ---
        page_obj = paginate_results(all_content_dicts, page_number, ITEMS_PER_PAGE)

        # --- Get Data for Filters ---
        all_providers_queryset = get_providers_for_region_filter(selected_region)

        providers_for_context = []
        for provider in all_providers_queryset:
            providers_for_context.append({
                'tmdb_id': provider.tmdb_id,
                'name': provider.name,
                'logo_url': get_provider_logo_url(provider.logo_path)
            })
        # --- Prepare Filters for Pagination ---
        current_filters_encoded = encode_filters_for_pagination(request.GET)

        # --- Prepare Context ---
        context = {
            'page_obj': page_obj,
            'selected_region': selected_region,
            'REGION_CHOICES': REGION_CHOICES,
            'watchlist_ids': watchlist_ids,
            'MEDIA_URL': settings.MEDIA_URL,
            # Add filter data and selections
            'all_providers': providers_for_context,
            'selected_provider_ids': selected_provider_ids,
            # Add encoded filters
            'current_filters_encoded': current_filters_encoded,
        }
        return render(request, 'popular.html', context)

    except Exception as e:
        print(f"Error in popular view: {str(e)}")
        # Simplified error context preparation
        error_region = request.GET.get('region', 'US')
        all_providers_region_error = []
        try:
            # Try to get providers even on error for form consistency
            all_providers_region_error = get_providers_for_region_filter(error_region)
        except Exception:
             print(f"Could not fetch providers for error page in region {error_region}")
        error_selected_ids = []
        error_provider_ids_str = request.GET.getlist('provider')
        for pid_str in error_provider_ids_str:
             if pid_str.isdigit():
                 error_selected_ids.append(int(pid_str))
        return render(request, 'popular.html', {
            'error': 'An unexpected error occurred while loading popular content.',
            'selected_region': error_region,
            'REGION_CHOICES': REGION_CHOICES,
            'page_obj': None,
            # Pass filter data if available
            'all_providers': all_providers_region_error,
            'selected_provider_ids': error_selected_ids,
            'current_filters_encoded': encode_filters_for_pagination(request.GET), # Pass filters
        })

def trending(request):
    """View for trending movies and TV shows."""
    try:
        region = request.GET.get('region', 'NO')
        tmdb = TMDBClient()
        watchlist_ids = get_watchlist_ids(request.user)
        
        # Get trending content for the week
        movies = tmdb.get_trending_movies()['results'][:10]  # Get top 10
        tv_shows = tmdb.get_trending_tv_shows()['results'][:10]  # Get top 10
        
        # Process results with streaming info
        processed_movies = []
        processed_tv_shows = []
        
        for movie in movies:
            movie['media_type'] = 'movie'
            result = tmdb.process_content_item(movie, region)
            # Convert ID to string for comparison
            result['id'] = str(result['id'])
            processed_movies.append(result)
            
        for show in tv_shows:
            show['media_type'] = 'tv'
            result = tmdb.process_content_item(show, region)
            # Convert ID to string for comparison
            result['id'] = str(result['id'])
            processed_tv_shows.append(result)
        
        return render(request, 'trending.html', {
            'movies': processed_movies,
            'tv_shows': processed_tv_shows,
            'selected_region': region,
            'watchlist_ids': watchlist_ids
        })
    except Exception as e:
        print(f"Error fetching trending content: {e}")
        return render(request, 'trending.html', {
            'error': 'Failed to load trending content',
            'selected_region': region
        })

# The view for movie and tv detailed information 
def content_detail(request, media_type, media_id):
    if media_id == 0:
        return redirect('index')
    try:
        tmdb = TMDBClient()
        region = request.GET.get('region', 'NO')
        watchlist_ids = get_watchlist_ids(request.user)
        
        # Get detailed content information
        content = tmdb.get_content_details(media_type, media_id)
        if not content:
            raise Http404("Content not found")

        # Get cast, for now only 5 
        cast = content.get('credits', {}).get('cast', [])[:5]

        # Process content
        processed_content = tmdb.process_content_item({
            'id': content['id'],
            'title': content.get('title') or content.get('name'),
            'media_type': media_type,
            'overview': content.get('overview'),
            'poster_path': content.get('poster_path'),
            'popularity': content.get('popularity'),
            'vote_average': content.get('vote_average'),
            'vote_count': content.get('vote_count')
        }, region)
        
        # Convert ID to string for comparison
        processed_content['id'] = str(processed_content['id'])
        is_in_watchlist = processed_content['id'] in watchlist_ids
        
       # Get creators and creators
        director = None
        if 'credits' in content:
            if media_type == 'movie':
                directors = [
                    crew.get('name') for crew in content['credits'].get('crew', [])
                    if crew.get('job') == 'Director'
                ]
                director = ", ".join(directors)
            elif media_type == 'tv':
                creators = content.get('created_by', [])
                director = ", ".join([c.get('name') for c in creators])

        processed_content['director'] = director
        processed_content['cast'] = cast 

        # Add realease data, runtime, genres and production companies for movies and tv shows
        if media_type == 'movie':
            processed_content.update({
                'release_date': content.get('release_date'),
                'runtime': content.get('runtime'),
                'genres': content.get('genres', []),
                'production_companies': content.get('production_companies', [])
            })
        else:
            processed_content.update({
                'first_air_date': content.get('first_air_date'),
                'last_air_date': content.get('last_air_date'),
                'number_of_seasons': content.get('number_of_seasons'),
                'number_of_episodes': content.get('number_of_episodes'),
                'genres': content.get('genres', []),
                'networks': content.get('networks', [])
            })
        
        return render(request, 'content_detail.html', {
            'content': processed_content,
            'media_type': media_type,
            'is_in_watchlist': is_in_watchlist,
            'selected_region': region,
            'watchlist_ids': watchlist_ids
        })
        
    except Exception as e:
        print(f"Error fetching content details: {e}")
        raise Http404("Content not found")

def actor_detail(request, actor_name):
    tmdb = TMDBClient()
    clean_actor_name = unquote(actor_name)

    try:
        search_result = tmdb._make_request("search/person", params={"query": clean_actor_name})
        person = search_result["results"][0] if search_result.get("results") else None

        if not person:
            raise Http404("Actor not found")

        person_id = person["id"]

        credits = tmdb._make_request(f"person/{person_id}/combined_credits")
        acting_roles = credits.get("cast", [])

        # split into movie and tv shows 
        movies = [c for c in acting_roles if c.get("media_type") == "movie"]
        shows = [c for c in acting_roles if c.get("media_type") == "tv"]

        # Sort by popularity 
        movies.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        shows.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        
        return render(request, "actor_detail.html", {
            "actor": clean_actor_name,
            "movies": movies,
            "shows": shows,
            "profile_path": person.get("profile_path") 
        })

    except Exception as e:
        print("Error fetching actor info:", e)
        raise Http404("Actor not found")
    
def director_detail(request, director_name):
    tmdb = TMDBClient()
    clean_director_name = unquote(director_name)

    try:
        # Search for the director
        search_result = tmdb._make_request("search/person", params={"query": clean_director_name})
        person = search_result["results"][0] if search_result.get("results") else None

        if not person:
            raise Http404("Director not found")

        person_id = person["id"]

        # Fetch credits from movie and tv show 
        credits = tmdb._make_request(f"person/{person_id}/combined_credits")
        directing_roles = [
            item for item in credits.get("crew", []) if item.get("job") == "Director"
        ]

        # Seperate movie and tv show 
        movies = [item for item in directing_roles if item.get("media_type") == "movie"]
        shows = [item for item in directing_roles if item.get("media_type") == "tv"]

        # Sort after popularity 
        movies.sort(key=lambda x: x.get("popularity", 0), reverse=True)
        shows.sort(key=lambda x: x.get("popularity", 0), reverse=True)

        return render(request, "director_detail.html", {
            "director": clean_director_name,
            "movies": movies,
            "shows": shows,
            "profile_path": person.get("profile_path")
        })

    except Exception as e:
        print(f"Error fetching director info: {e}")
        raise Http404("Director not found")

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'login.html', {
                'error': 'Invalid username or password'
            })
    
    return render(request, 'login.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')

    streaming_services = StreamingService.objects.all() 
    print("Streaming services in view:", streaming_services) 

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validate passwords match
        if password1 != password2:
            return render(request, 'register.html', {
                'error': 'Passwords do not match' 
            })

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already exists' 
                
            })

        # Create the user
        user = User.objects.create_user(username=username, password=password1, email=email)

        # Log in the new user
        login(request, user)
        return redirect('index')
    
    return render(request, 'register.html') 

#login/register
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
    if form.is_valid():
        user = form.save() 
        login(request, user) 
        return redirect('home') 
    else:
        form = UserCreationForm()
        return render(request, 'register.html', {'form': form})
@login_required


def profile_view(request):
    """View for user dashboard/profile."""
    # Get watchlist statistics
    watchlist_items = WatchlistItem.objects.filter(user=request.user)
    watchlist_count = watchlist_items.count()
    movie_count = watchlist_items.filter(media_type='movie').count()
    tv_count = watchlist_items.filter(media_type='tv').count()
    
    # Get recent activity, last 5 
    recent_items = watchlist_items.order_by('-added_date')[:5]
    
    # Get watched movies statistics
    watched_items = WatchedMovie.objects.filter(user=request.user)
    watched_count = watched_items.count()
    watched_movie_count = watched_items.filter(media_type='movie').count()
    watched_tv_count = watched_items.filter(media_type='tv').count()
    
    # Sum all runtime values that are not None
    total_watch_minutes = watched_items.filter(runtime__isnull=False).aggregate(total=models.Sum('runtime'))['total'] or 0
    
    # For items without runtime, use average estimates
    items_without_runtime = watched_items.filter(runtime__isnull=True)
    movies_without_runtime = items_without_runtime.filter(media_type='movie').count()
    tv_without_runtime = items_without_runtime.filter(media_type='tv').count()
    
    # Use average of 120 minutes for movies and 400 minutes for TV shows (10 episodes × 40 minutes)
    estimated_minutes = (movies_without_runtime * 120) + (tv_without_runtime * 400)
    total_watch_minutes += estimated_minutes
    
    # Convert minutes to hours and minutes for display
    total_watch_hours = total_watch_minutes // 60
    remaining_minutes = total_watch_minutes % 60
    
    # Get recent watched items, last 5 
    recent_watched = watched_items.order_by('-watched_date')[:5]
    
    # Get the number of reviews written 
    reviews_written = watched_items.filter(review__isnull=False).exclude(review='').count()
    
    # Check badges and award them if criteria are met
    from myapp.models import Badge, UserBadge
    
    # Check for movie milestone badges
    movie_milestone_badges = Badge.objects.filter(
        requirement_type='movies_watched'
    ).order_by('requirement_count')
    
    for badge in movie_milestone_badges:
        if watched_movie_count >= badge.requirement_count:
            # Award badge if not already awarded
            UserBadge.objects.get_or_create(user=request.user, badge=badge)
    
    # Check for TV show milestone badges
    tv_milestone_badges = Badge.objects.filter(
        requirement_type='tv_shows_watched'
    ).order_by('requirement_count')
    
    for badge in tv_milestone_badges:
        if watched_tv_count >= badge.requirement_count:
            # Award badge if not already awarded
            UserBadge.objects.get_or_create(user=request.user, badge=badge)
    
    # Check for review badges
    review_badges = Badge.objects.filter(
        requirement_type='reviews_written'
    ).order_by('requirement_count')
    
    for badge in review_badges:
        if reviews_written >= badge.requirement_count:
            # Award badge if not already awarded
            UserBadge.objects.get_or_create(user=request.user, badge=badge)
    
    # Check for watch time badges
    watch_time_badges = Badge.objects.filter(
        requirement_type='watch_hours'
    ).order_by('requirement_count')
    
    for badge in watch_time_badges:
        if total_watch_hours >= badge.requirement_count:
            # Award badge if not already awarded
            UserBadge.objects.get_or_create(user=request.user, badge=badge)
    
    # Get all badges the user has earned
    user_badges = UserBadge.objects.filter(user=request.user).select_related('badge')
    
    # Get the most recently earned badges (for display)
    recent_badges = user_badges.order_by('-earned_date')[:3]
    
    # Calculate progress to next badge for each category
    next_movie_badge = None
    movie_badge_progress = 0
    for badge in movie_milestone_badges:
        if watched_movie_count < badge.requirement_count:
            next_movie_badge = badge
            movie_badge_progress = (watched_movie_count / badge.requirement_count) * 100
            break
    
    next_tv_badge = None
    tv_badge_progress = 0
    for badge in tv_milestone_badges:
        if watched_tv_count < badge.requirement_count:
            next_tv_badge = badge
            tv_badge_progress = (watched_tv_count / badge.requirement_count) * 100
            break
    
    next_review_badge = None
    review_badge_progress = 0
    for badge in review_badges:
        if reviews_written < badge.requirement_count:
            next_review_badge = badge
            review_badge_progress = (reviews_written / badge.requirement_count) * 100
            break
    
    next_watch_time_badge = None
    watch_time_progress = 0
    for badge in watch_time_badges:
        if total_watch_hours < badge.requirement_count:
            next_watch_time_badge = badge
            watch_time_progress = (total_watch_hours / badge.requirement_count) * 100
            break

    # Handle marking content as watched directly from profile
    if request.method == 'POST' and 'mark_watched' in request.POST:
        media_id = request.POST.get('media_id')
        media_type = request.POST.get('media_type')
        title = request.POST.get('title')
        poster_path = request.POST.get('poster_path')
        
        # Check if already watched
        existing = WatchedMovie.objects.filter(
            user=request.user,
            media_id=media_id,
            media_type=media_type
        ).first()
        
        if not existing:
            # If not watched, add it to watched list
            # Try to get runtime from TMDB API
            runtime = None
            try:
                tmdb = TMDBClient()
                content = tmdb.get_content_details(media_type, media_id)
                if content:
                    # Movies have 'runtime', TV shows have 'episode_run_time'
                    if media_type == 'movie':
                        runtime = content.get('runtime')
                    else:
                        # For TV shows, use average episode runtime * number of episodes in first season
                        episode_runtimes = content.get('episode_run_time', [])
                        if episode_runtimes:
                            avg_episode_runtime = sum(episode_runtimes) / len(episode_runtimes)
                            # Get number of episodes in first season if available
                            seasons = content.get('seasons', [])
                            if seasons:
                                for season in seasons:
                                    if season.get('season_number') == 1:
                                        episodes = season.get('episode_count', 10)
                                        runtime = int(avg_episode_runtime * episodes)
                                        break
                                else:
                                    # If no season 1 found, estimate as 10 episodes
                                    runtime = int(avg_episode_runtime * 10)
            except Exception as e:
                print(f"Error fetching runtime from TMDB: {e}")
                
            WatchedMovie.objects.create(
                user=request.user,
                media_id=media_id,
                media_type=media_type,
                title=title,
                poster_path=poster_path,
                runtime=runtime  # Store the runtime we fetched
            )
            
            # Remove from watchlist
            WatchlistItem.objects.filter(
                user=request.user,
                media_id=media_id,
                media_type=media_type
            ).delete()
        
        return redirect('profile')
    
    # Handle rating content
    if request.method == 'POST' and 'rate_content' in request.POST:
        media_id = request.POST.get('media_id')
        rating = request.POST.get('rating')
        review = request.POST.get('review') 
        
        try:
            watched_item = WatchedMovie.objects.get(
                user=request.user,
                media_id=media_id
            )
            
            watched_item.rating = rating
            watched_item.rated_date = timezone.now()
            watched_item.review = review 
            watched_item.save()
            
        except WatchedMovie.DoesNotExist:
            pass
        
        return redirect('profile')
    
    # Handle removing item from watchlist
    if request.method == 'POST' and 'remove_watchlist' in request.POST:
        media_id = request.POST.get('media_id')
        media_type = request.POST.get('media_type')
        
        # Delete the watchlist item
        item = WatchlistItem.objects.filter(
            user=request.user,
            media_id=media_id,
            media_type=media_type
        ).first()
        
        if item:
            title = item.title
            item.delete()
        
        return redirect('profile')
        
    # Handle removing item from watched list
    if request.method == 'POST' and 'remove_watched' in request.POST:
        media_id = request.POST.get('media_id')
        media_type = request.POST.get('media_type')
        
        # Delete the watched item
        item = WatchedMovie.objects.filter(
            user=request.user,
            media_id=media_id,
            media_type=media_type
        ).first()
        
        if item:
            title = item.title
            item.delete()
        
        # Use absolute URL path instead of URL name with query string
        return redirect('/profile/?show=watched')
    
    # Check if we're showing watched content
    show_watched = request.GET.get('show', '') == 'watched'
    
    if show_watched:
        # Paginate watched items for the watched tab
        paginator = Paginator(watched_items, 12)  # 12 items per page
        page = request.GET.get('page', 1)
        
        try:
            items_page = paginator.page(page)
        except EmptyPage:
            items_page = paginator.page(paginator.num_pages)
            
        display_items = items_page
    else:
        # Paginate watchlist items for the watchlist tab
        paginator = Paginator(watchlist_items, 12)  # 12 items per page
        page = request.GET.get('page', 1)
        
        try:
            items_page = paginator.page(page)
        except EmptyPage:
            items_page = paginator.page(paginator.num_pages)
            
        display_items = items_page
    
    context = {
        'watchlist_count': watchlist_count,
        'movie_count': movie_count,
        'tv_count': tv_count,
        'recent_items': recent_items,
        'watched_count': watched_count,
        'watched_movie_count': watched_movie_count,
        'watched_tv_count': watched_tv_count,
        'recent_watched': recent_watched,
        'show_watched': show_watched,
        'display_items': display_items,
        'total_watch_minutes': total_watch_minutes,
        'total_watch_hours': total_watch_hours,
        'remaining_minutes': remaining_minutes,
        'reviews_written': reviews_written,
        'user_badges': user_badges,
        'recent_badges': recent_badges,
        'badge_count': user_badges.count(),
        'next_movie_badge': next_movie_badge,
        'movie_badge_progress': movie_badge_progress,
        'next_tv_badge': next_tv_badge,
        'tv_badge_progress': tv_badge_progress,
        'next_review_badge': next_review_badge,
        'review_badge_progress': review_badge_progress,
        'next_watch_time_badge': next_watch_time_badge,
        'watch_time_progress': watch_time_progress,
    }
    
    return render(request, 'profile.html', context)

#watchlist stuff
@login_required
def watchlist(request):
    """View to display user's watchlist"""
    items = WatchlistItem.objects.filter(user=request.user).order_by('-added_date')
    return render(request, 'watchlist.html', {'watchlist': items})

@login_required
@require_POST
def add_to_watchlist(request, media_type, media_id):
    """Add an item to watchlist, The item are stored in database, many to many relationship"""
    if media_type not in ['movie', 'tv']:
        return JsonResponse({'error': 'Invalid media type'}, status=400)
    
    title = request.POST.get('title')
    poster_path = request.POST.get('poster_path')
    # Normalize local poster URLs to relative path
    if poster_path and poster_path.startswith(request.build_absolute_uri(settings.MEDIA_URL)):
        poster_path = poster_path.replace(request.build_absolute_uri(settings.MEDIA_URL), 'media/')
    if poster_path and poster_path.startswith(settings.MEDIA_URL):
        poster_path = poster_path[len(settings.MEDIA_URL):] if poster_path.startswith(settings.MEDIA_URL) else poster_path
    # Check if item already exists
    existing_item = WatchlistItem.objects.filter(
        user=request.user,
        media_id=media_id,
        media_type=media_type
    ).first()
    
    if existing_item:
        # If item exists, remove it
        existing_item.delete()
        message = 'removed'
    else:
        # If item doesn't exist, add it
        WatchlistItem.objects.create(
            user=request.user,
            media_id=media_id,
            media_type=media_type,
            title=title,
            poster_path=poster_path
        )
        message = 'added'
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': message,  # Changed from status to message
            'media_id': media_id,
            'media_type': media_type,
            'title': title
        })
    
    return redirect(request.META.get('HTTP_REFERER', 'index'))

@login_required
@require_POST
def remove_from_watchlist(request, media_type, media_id):
    """Remove an item from watchlist"""
    try:
        item = get_object_or_404(
            WatchlistItem, 
            user=request.user,
            media_type=media_type,
            media_id=media_id
        )
        title = item.title  # Get the title before deleting
        item.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'removed',
                'media_id': media_id,
                'media_type': media_type,
                'title': title
            })
        
        return redirect(request.META.get('HTTP_REFERER', 'watchlist'))
    
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

def contact(request):
    if request.method == 'POST':
        # Here you would typically handle the contact form submission
        # For example, send an email or save to database
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Add your contact form processing logic here
        # For now, just redirect back to the contact page
        return redirect('contact')
    
    return render(request, 'contact.html')

def privacy(request):
    return render(request, 'privacy.html')

def about(request):
    return render(request, 'about.html')

@login_required
def my_available_content(request):
    user_services = request.user.streaming_services.all()  # Ensure 'streaming_services' is correct
    movies = []  # Placeholder for future logic
    shows = []   # Placeholder for future logic
    return render(request, 'my_available_content.html', {
        'user_services': user_services,
        'movies': movies,
        'shows': shows
    })


@login_required
def settings_view(request):
    # NOT IN USE 
    all_services = StreamingService.objects.all()
    selected_services = request.user.streaming_services.values_list('id', flat=True)

    return render(request, 'settings.html', {
        'streaming_services': all_services,
        'selected_services': selected_services
    })

@login_required
def send_friend_request_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            to_user = User.objects.get(username=username)
            
            # Check if users are already friends
            if request.user.get_friends().filter(id=to_user.id).exists():
                messages.info(request, f"You are already friends with {username}")
                return redirect('profile')
                
            # Check if there's a pending request
            existing_request = FriendRequest.objects.filter(
                from_user=request.user, 
                to_user=to_user, 
                status='pending'
            ).exists()
            
            if existing_request:
                messages.info(request, f"You already sent a friend request to {username}")
                return redirect('profile')
                
            if request.user.send_friend_request(to_user):
                messages.success(request, f"Friend request sent to {username}")
            else:
                messages.error(request, "Friend request could not be sent")
        except User.DoesNotExist:
            messages.error(request, f"User {username} does not exist")
        
        return redirect('profile')
    
    return render(request, 'profile.html')

@login_required
def accept_friend_request_view(request, request_id):
    try:
        friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user, status='pending')
        if request.user.accept_friend_request(friend_request.from_user):
            messages.success(request, f"You are now friends with {friend_request.from_user.username}")
        else:
            messages.error(request, "Could not accept friend request")
    except FriendRequest.DoesNotExist:
        messages.error(request, "Friend request does not exist")
    
    return redirect('profile')

@login_required
def reject_friend_request_view(request, request_id):
    try:
        friend_request = FriendRequest.objects.get(id=request_id, to_user=request.user, status='pending')
        if request.user.reject_friend_request(friend_request.from_user):
            messages.success(request, f"Friend request from {friend_request.from_user.username} rejected")
        else:
            messages.error(request, "Could not reject friend request")
    except FriendRequest.DoesNotExist:
        messages.error(request, "Friend request does not exist")
    
    return redirect('profile')

@login_required
def unfriend_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        try:
            friend = User.objects.get(username=username)
            if request.user.unfriend(friend):
                messages.success(request, f"You are no longer friends with {username}")
            else:
                messages.error(request, "Could not remove friend")
        except User.DoesNotExist:
            messages.error(request, f"User {username} does not exist")
        
        return redirect('profile')
    
    return render(request, 'profile.html')

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        user = request.user
        
        # Verify password before deletion
        if user.check_password(password):
            # Log the user out and delete account
            logout(request)
            user.delete()
            messages.success(request, "Your account has been deleted.")
            return redirect('index')
        else:
            messages.error(request, "Incorrect password. Account deletion cancelled.")
            
    return render(request, 'delete_account.html')

@login_required
def change_password_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Check if the old password is correct
        if not request.user.check_password(old_password):
            messages.error(request, "Your old password was entered incorrectly.")
            return render(request, 'change_password.html')
            
        # Check if the new passwords match
        if new_password1 != new_password2:
            messages.error(request, "The two password fields didn't match.")
            return render(request, 'change_password.html')
            
        # Update the password
        request.user.set_password(new_password1)
        request.user.save()
        
        # Update the session so the user doesn't get logged out
        update_session_auth_hash(request, request.user)
        
        messages.success(request, "Your password was successfully updated!")
        return redirect('settings')
        
    return render(request, 'change_password.html')


# NOT IN USE / Later development 
@login_required
def update_streaming_services(request):
    user = request.user
    all_services = StreamingService.objects.all()

    if request.method == 'POST':
        selected_service_ids = request.POST.getlist('services')
        user.streaming_services.set(selected_service_ids)
        return redirect('settings')

    return render(request, 'settings.html', {
        'streaming_services': all_services,
        'selected_services': user.streaming_services.values_list('id', flat=True)
    })

@login_required
def my_friend_view(request, username):
    friend = get_object_or_404(User, username=username)

    # Watched content
    watched_items = WatchedMovie.objects.filter(user=friend)
    watched_count = watched_items.count()
    watched_movie_count = watched_items.filter(media_type='movie').count()
    watched_tv_count = watched_items.filter(media_type='tv').count()

    # Watch time
    total_watch_minutes = watched_items.filter(runtime__isnull=False).aggregate(
        total=models.Sum('runtime'))['total'] or 0

    items_without_runtime = watched_items.filter(runtime__isnull=True)
    total_watch_minutes += (
        items_without_runtime.filter(media_type='movie').count() * 120 +
        items_without_runtime.filter(media_type='tv').count() * 400
    )
    total_watch_hours = total_watch_minutes // 60
    remaining_minutes = total_watch_minutes % 60

    # Calculate number of reviews written
    reviews_written = watched_items.filter(review__isnull=False).exclude(review='').count()
    
    # Get all badges the friend has earned
    from myapp.models import UserBadge, Badge
    
    user_badges = UserBadge.objects.filter(user=friend).select_related('badge')
    
    # Get the most recently earned badges (for display)
    recent_badges = user_badges.order_by('-earned_date')[:3]
    
    # Calculate progress to next badge for each category
    movie_milestone_badges = Badge.objects.filter(
        requirement_type='movies_watched'
    ).order_by('requirement_count')
    
    tv_milestone_badges = Badge.objects.filter(
        requirement_type='tv_shows_watched'
    ).order_by('requirement_count')
    
    review_badges = Badge.objects.filter(
        requirement_type='reviews_written'
    ).order_by('requirement_count')
    
    watch_time_badges = Badge.objects.filter(
        requirement_type='watch_hours'
    ).order_by('requirement_count')
    
    next_movie_badge = None
    movie_badge_progress = 0
    for badge in movie_milestone_badges:
        if watched_movie_count < badge.requirement_count:
            next_movie_badge = badge
            movie_badge_progress = (watched_movie_count / badge.requirement_count) * 100
            break
    
    next_tv_badge = None
    tv_badge_progress = 0
    for badge in tv_milestone_badges:
        if watched_tv_count < badge.requirement_count:
            next_tv_badge = badge
            tv_badge_progress = (watched_tv_count / badge.requirement_count) * 100
            break
    
    next_review_badge = None
    review_badge_progress = 0
    for badge in review_badges:
        if reviews_written < badge.requirement_count:
            next_review_badge = badge
            review_badge_progress = (reviews_written / badge.requirement_count) * 100
            break
    
    next_watch_time_badge = None
    watch_time_progress = 0
    for badge in watch_time_badges:
        if total_watch_hours < badge.requirement_count:
            next_watch_time_badge = badge
            watch_time_progress = (total_watch_hours / badge.requirement_count) * 100
            break

    # Watched content to display (for the content grid)
    recent_watched = watched_items.order_by('-watched_date')[:12]

    context = {
        'friend': friend,
        'watched_count': watched_count,
        'watched_movie_count': watched_movie_count,
        'watched_tv_count': watched_tv_count,
        'total_watch_hours': total_watch_hours,
        'remaining_minutes': remaining_minutes,
        'recent_watched': recent_watched,
        'reviews_written': reviews_written,
        'user_badges': user_badges,
        'recent_badges': recent_badges,
        'badge_count': user_badges.count(),
        'next_movie_badge': next_movie_badge,
        'movie_badge_progress': movie_badge_progress,
        'next_tv_badge': next_tv_badge,
        'tv_badge_progress': tv_badge_progress,
        'next_review_badge': next_review_badge,
        'review_badge_progress': review_badge_progress,
        'next_watch_time_badge': next_watch_time_badge,
        'watch_time_progress': watch_time_progress,
    }

    return render(request, 'my_friend.html', context)


# Custom error handlers
def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500) 
