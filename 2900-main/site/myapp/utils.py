"""
Utility functions for the MovieVikings application.

This module contains helper functions for:
- Processing streaming provider data
- Handling image URLs
- Region validation
- Content filtering and pagination
- Provider management
"""

from django.conf import settings
from .models import REGION_CHOICES, MovieProvider, TVShowProvider, Movie
from django.db.models import Prefetch, Q, QuerySet
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Movie, TVShow, MovieProvider, TVShowProvider, StreamingProvider
from django.conf import settings
from typing import List, Dict, Any, Optional, Union

# Genre IDs to exclude from TV show results
NEWS_GENRE_ID = 10763
TALK_GENRE_ID = 10767

def process_providers(streaming_info_dict):
    """
    Process streaming provider data into a standardized format.
    
    Args:
        streaming_info_dict: Dictionary containing streaming provider information
        
    Returns:
        dict: Processed provider data with flatrate and rent options
    """
    result = {
        'flatrate': [],
        'rent': [],
        'available': False
    }
    
    for provider_rel in streaming_info_dict.get('flatrate', []):
        provider = provider_rel.provider
        result['flatrate'].append({
            'provider_name': provider.name,
            'logo_path': provider.logo_path,
            'provider_url': f"https://www.themoviedb.org/provider/{provider.tmdb_id}"
        })
    
    for provider_rel in streaming_info_dict.get('rent', []):
        provider = provider_rel.provider
        result['rent'].append({
            'provider_name': provider.name,
            'logo_path': provider.logo_path,
            'provider_url': f"https://www.themoviedb.org/provider/{provider.tmdb_id}"
        })
    
    result['available'] = bool(result['flatrate'] or result['rent'])
    return result

def get_poster_url(poster_path):
    """
    Format poster URL based on the path type.
    
    Args:
        poster_path: Path to the poster image
        
    Returns:
        str: Complete URL to the poster image, or None if no path provided
    """
    if not poster_path:
        return None
    if poster_path.startswith('posters/'):
        return f"{settings.MEDIA_URL}{poster_path}"
    if poster_path.startswith(('http://', 'https://')):
        return poster_path
    return f"https://image.tmdb.org/t/p/w500{poster_path}"

def format_provider(provider):
    """
    Format provider data with correct logo path.
    
    Args:
        provider: Dictionary containing provider information
        
    Returns:
        dict: Formatted provider data with complete logo URL
    """
    logo_path = provider.get('logo_path', '')
    if logo_path.startswith('providers/'):
        final_logo_path = f"{settings.MEDIA_URL}{logo_path}"
    else:
        final_logo_path = f"https://image.tmdb.org/t/p/original{logo_path}"
        
    return {
        'provider_name': provider.get('provider_name', ''),
        'provider_url': provider.get('provider_url', ''),
        'logo_path': final_logo_path
    }

def get_validated_region(request) -> str:
    """
    Get and validate region from request parameters.
    
    Args:
        request: HTTP request object containing region parameter
        
    Returns:
        str: Validated region code, defaults to 'US' if invalid
    """
    region_param = request.GET.get('region', None)
    default_region = 'US'
    if region_param:
        region_param_upper = region_param.upper()
        valid_regions = {code for code, name in REGION_CHOICES}
        if region_param_upper in valid_regions:
            return region_param_upper
    return default_region

def get_popular_movies(region: str, limit: int, selected_provider_ids: Optional[List[int]] = None) -> QuerySet[Movie]:
    """
    Get popular movies filtered by region and providers.
    
    Args:
        region: Region code to filter by
        limit: Maximum number of results to return
        selected_provider_ids: Optional list of provider IDs to filter by
        
    Returns:
        QuerySet[Movie]: Filtered and prefetched movie queryset
    """
    movies_qs = Movie.objects.prefetch_related('genres')
    movies_qs = movies_qs.filter(streaming_info__region=region)

    if selected_provider_ids:
        movies_qs = movies_qs.filter(
            streaming_info__provider__tmdb_id__in=selected_provider_ids
        )

    return (
        movies_qs
        .distinct()
        .prefetch_related(
            Prefetch(
                'streaming_info',
                queryset=MovieProvider.objects.filter(region=region).select_related('provider'),
                to_attr='providers_list'
            )
        )
    )

def get_popular_tv_shows(region: str, limit: int, selected_provider_ids: Optional[List[int]] = None) -> QuerySet[TVShow]:
    """
    Get popular TV shows filtered by region and providers.
    
    Excludes news and talk shows by default.
    
    Args:
        region: Region code to filter by
        limit: Maximum number of results to return
        selected_provider_ids: Optional list of provider IDs to filter by
        
    Returns:
        QuerySet[TVShow]: Filtered and prefetched TV show queryset
    """
    tv_shows_qs = (
        TVShow.objects
        .exclude(Q(genres__tmdb_id=NEWS_GENRE_ID) | Q(genres__tmdb_id=TALK_GENRE_ID))
        .prefetch_related('genres')
    )
    tv_shows_qs = tv_shows_qs.filter(streaming_info__region=region)

    if selected_provider_ids:
        tv_shows_qs = tv_shows_qs.filter(
            streaming_info__provider__tmdb_id__in=selected_provider_ids
        )
    return (
        tv_shows_qs
        .distinct()
        .prefetch_related(
            Prefetch(
                'streaming_info',
                queryset=TVShowProvider.objects.filter(region=region).select_related('provider'),
                to_attr='providers_list'
            )
        )
    )

def get_provider_logo_url(logo_path: Optional[str]) -> Optional[str]:
    """
    Construct the full provider logo URL from a path.
    
    Args:
        logo_path: Path to the provider logo
        
    Returns:
        str: Complete URL to the provider logo, or None if no path provided
    """
    if not logo_path or logo_path == 'None':
        return None
    base_url = "https://image.tmdb.org/t/p/w92"
    return f"{base_url}{logo_path}" if logo_path.startswith('/') else f"{base_url}/{logo_path}"

def _extract_providers_for_item(item: Union[Movie, TVShow]) -> Dict[str, Any]:
    """
    Extract and format streaming provider info from a prefetched item.
    
    Args:
        item: Movie or TVShow object with prefetched providers
        
    Returns:
        dict: Formatted provider information including availability status
    """
    providers: Dict[str, Any] = {'flatrate': [], 'rent': [], 'buy': [], 'available': False}
    for provider_info in getattr(item, 'providers_list', []):
        logo_url = get_provider_logo_url(provider_info.provider.logo_path)
        provider_data = {
            'provider_name': provider_info.provider.name,
            'logo_path': logo_url,
            'provider_id': provider_info.provider.tmdb_id
        }
        if provider_info.type in providers:
            providers[provider_info.type].append(provider_data)

    providers['available'] = any(providers.get(ptype) for ptype in ['flatrate', 'rent', 'buy'])
    return providers

def process_content_item(item: Union[Movie, TVShow], watchlist_ids: List[str], media_type: str) -> Dict[str, Any]:
    """
    Convert a Movie or TVShow object into a dictionary for template rendering.
    
    Args:
        item: Movie or TVShow object to process
        watchlist_ids: List of media IDs in user's watchlist
        media_type: Type of content ('movie' or 'tv')
        
    Returns:
        dict: Processed content item with all necessary information for display
    """
    providers = _extract_providers_for_item(item)
    poster_url = get_poster_url(item.poster_path)

    rating = float(item.rating) if item.rating is not None else 0.0
    popularity = float(item.popularity) if item.popularity is not None else 0.0
    release_date = item.release_date if media_type == 'movie' else getattr(item, 'first_air_date', None)

    return {
        'id': str(item.tmdb_id),
        'title': item.title,
        'overview': item.overview,
        'poster_url': poster_url,
        'rating': rating,
        'vote_count': item.vote_count or 0,
        'release_date': release_date,
        'media_type': media_type,
        'popularity': popularity,
        'streaming_providers': providers,
        'in_watchlist': str(item.tmdb_id) in watchlist_ids,
    }

def paginate_results(items: List[Dict[str, Any]], page_number: int, items_per_page: int) -> Paginator:
    """
    Paginate a list of dictionaries and handle page errors.
    
    Args:
        items: List of items to paginate
        page_number: Current page number
        items_per_page: Number of items per page
        
    Returns:
        Paginator: Paginated results object
    """
    paginator = Paginator(items, items_per_page)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj

def get_providers_for_region_filter(region: str) -> QuerySet[StreamingProvider]:
    """
    Get distinct providers available for any content in the specified region.
    
    Fetches providers that are linked to either movies or TV shows in the region,
    ordered by provider name.
    
    Args:
        region: Region code to filter by
        
    Returns:
        QuerySet[StreamingProvider]: Filtered and ordered provider queryset
    """
    # Get TMDB IDs of providers linked to movies in the region
    movie_provider_tmdb_ids = set(MovieProvider.objects.filter(
        region=region
    ).values_list('provider__tmdb_id', flat=True))

    # Get TMDB IDs of providers linked to TV shows in the region
    tv_provider_tmdb_ids = set(TVShowProvider.objects.filter(
        region=region
    ).values_list('provider__tmdb_id', flat=True))

    # Combine the sets of TMDB IDs
    available_provider_tmdb_ids = movie_provider_tmdb_ids.union(tv_provider_tmdb_ids)

    # Filter StreamingProvider using the collected TMDB IDs
    return StreamingProvider.objects.filter(
        tmdb_id__in=available_provider_tmdb_ids
    ).distinct().order_by('name')

def encode_filters_for_pagination(request_get_dict) -> str:
    """
    Encode GET parameters (excluding 'page') for pagination links.
    
    Args:
        request_get_dict: Dictionary of GET parameters
        
    Returns:
        str: URL-encoded query string for pagination
    """
    query_params = request_get_dict.copy()
    if 'page' in query_params:
        del query_params['page']
    return query_params.urlencode()