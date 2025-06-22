"""
TMDB API Client for MovieVikings application.

This module provides a client for interacting with The Movie Database (TMDB) API.
It handles all API requests, caching, and data processing for movie and TV show information.
"""

import os
import requests
from typing import Dict, Optional
from django.core.cache import cache

class TMDBClient:
    """
    Client for interacting with The Movie Database (TMDB) API.
    
    This class handles all communication with the TMDB API, including:
    - Authentication and request management
    - Content fetching and processing
    - Caching of API responses
    - Streaming provider information
    """
    
    BASE_URL = "https://api.themoviedb.org/3"
    
    # Mapping of streaming providers to their respective URLs
    # Used for generating direct links to content on streaming platforms
    PROVIDER_URLS = {
        # Norway
        'Netflix': {
            'base_url': 'https://www.netflix.com/no/',
            'search_url': 'https://www.netflix.com/search?q={title}'
        },
        'HBO Max': {
            'base_url': 'https://www.hbomax.com/no/en',
            'search_url': 'https://www.hbomax.com/no/en/search?query={title}'
        },
        'Disney Plus': {
            'base_url': 'https://www.disneyplus.com/no/',
            'search_url': 'https://www.disneyplus.com/search?q={title}'
        },
        'Viaplay': {
            'base_url': 'https://viaplay.no/',
            'search_url': 'https://viaplay.no/search?query={title}'
        },
        'Amazon Prime Video': {
            'base_url': 'https://www.primevideo.com/',
            'search_url': 'https://www.primevideo.com/search/?phrase={title}'
        },
        'Apple TV Plus': {
            'base_url': 'https://tv.apple.com/no',
            'search_url': 'https://tv.apple.com/no/search?term={title}'
        },
        'TV 2 Play': {
            'base_url': 'https://play.tv2.no/',
            'search_url': 'https://play.tv2.no/programmer?q={title}'
        }
    }
    
    def __init__(self):
        """
        Initialize the TMDB client with API credentials.
        
        Raises:
            ValueError: If neither TMDB_API_KEY nor TMDB_ACCESS_TOKEN is set
        """
        self.api_key = os.environ.get('TMDB_API_KEY')
        self.access_token = os.environ.get('TMDB_ACCESS_TOKEN')
        
        if not (self.api_key or self.access_token):
            raise ValueError("Either TMDB_API_KEY or TMDB_ACCESS_TOKEN must be set in environment variables")
            
        self.headers = {
            'Authorization': f'Bearer {self.access_token}' if self.access_token else None,
            'accept': 'application/json'
        }
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a request to the TMDB API with caching.
        
        Args:
            endpoint: API endpoint to call
            params: Optional query parameters
            
        Returns:
            Dict: JSON response from the API
            
        Raises:
            requests.exceptions.RequestException: If the API request fails
        """
        # Create cache key from endpoint and params
        cache_key = f"tmdb_{endpoint}"
        if params:
            cache_key += "_" + "_".join(f"{k}:{v}" for k, v in sorted(params.items()))
        
        # Try to get from cache first
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            return cached_response
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        if self.api_key:
            params = params or {}
            params['api_key'] = self.api_key
            
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Cache the response for 15 minutes
        cache.set(cache_key, data, timeout=60 * 15)
        return data
    
    def get_popular_movies(self, page: int = 1) -> Dict:
        """
        Get a list of popular movies.
        
        Args:
            page: Page number of results to return
            
        Returns:
            Dict: Popular movies data from TMDB
        """
        return self._make_request('movie/popular', params={'page': page})
    
    def get_popular_tv_shows(self, page: int = 1) -> Dict:
        """
        Get a list of popular TV shows.
        
        Args:
            page: Page number of results to return
            
        Returns:
            Dict: Popular TV shows data from TMDB
        """
        return self._make_request('tv/popular', params={'page': page})
    
    def get_trending_movies(self, time_window: str = 'week') -> Dict:
        """
        Get trending movies.
        
        Args:
            time_window: 'day' or 'week' to specify the time period
            
        Returns:
            Dict: Trending movies data from TMDB
            
        Raises:
            ValueError: If time_window is not 'day' or 'week'
        """
        if time_window not in ['day', 'week']:
            raise ValueError("time_window must be either 'day' or 'week'")
        return self._make_request(f'trending/movie/{time_window}')
    
    def get_trending_tv_shows(self, time_window: str = 'week') -> Dict:
        """
        Get trending TV shows.
        
        Args:
            time_window: 'day' or 'week' to specify the time period
            
        Returns:
            Dict: Trending TV shows data from TMDB
            
        Raises:
            ValueError: If time_window is not 'day' or 'week'
        """
        if time_window not in ['day', 'week']:
            raise ValueError("time_window must be either 'day' or 'week'")
        return self._make_request(f'trending/tv/{time_window}')

    def _transform_collection_details(self, collection_details: dict) -> dict:
        """
        Transform collection details into a search-like result format.
        
        This function takes the 'parts' of a collection and formats them into a structure
        that matches the search results format, making it easier to process in the UI.
        
        Args:
            collection_details: Raw collection data from TMDB
            
        Returns:
            dict: Transformed collection data in search result format
        """
        movies = collection_details.get("parts", [])
        return {
            "page": 1,
            "total_results": len(movies),
            "total_pages": 1,
            "results": movies
        }

    def get_collection_movies(self, query: str) -> Dict:
        """
        Fetch movies from a franchise collection.
        
        Searches for a collection matching the query and returns all movies
        in that collection. Used for finding related movies in the same franchise.
        
        Args:
            query: Search term to find the collection
            
        Returns:
            Dict: Collection data with all movies in the franchise
        """
        # Search for collections
        collection_search = self._make_request("search/collection", params={"query": query})
        if not collection_search.get("results"):
            print(f"[WARNING]: No collection found for query '{query}'.")
            return {}
        
        # Choose the collection where the query matches the collection name if possible
        matching_collections = [
            coll for coll in collection_search["results"]
            if query.lower() in coll.get("name", "").lower()
        ]
        chosen_collection = matching_collections[0] if matching_collections else collection_search["results"][0]
        collection_id = chosen_collection["id"]
        
        # Retrieve collection details
        collection_details = self._make_request(f"collection/{collection_id}")
        collection = self._transform_collection_details(collection_details)
        return collection
    
    def keyword_search(self, query: str) -> Dict:
        """
        Search for content using keywords.
        
        Finds related keywords and returns content associated with those keywords.
        This helps find content that might not match the exact search terms.
        
        Args:
            query: Search term to find related keywords
            
        Returns:
            Dict: Content associated with the found keywords
        """
        # Search for related keywords
        keyword_search = self._make_request("search/keyword", params={"query": query})
        if not keyword_search.get("results"):
            print(f"[WARNING]: No keywords found for query '{query}'.")
            return {}
        top_keywords = keyword_search["results"][:3]
        # Get results for each keyword
        for keyword in top_keywords:
            keyword_id = keyword["id"]
            results = self._make_request(
                "discover/movie",
                params={"with_keywords": keyword_id}
            )
        return results

    def search(self, query: str, search_type: str = 'multi', page: int = 1) -> Dict:
        """
        Search for movies, TV shows, or both.
        
        Performs a comprehensive search across multiple endpoints:
        1. Collection search for franchise movies
        2. Keyword search for related content
        3. Title search for direct matches
        
        Args:
            query: Search term
            search_type: 'movie', 'tv', or 'multi' (both movies and TV shows)
            page: Page number of results to return
            
        Returns:
            Dict: Combined search results from all search methods
            
        Raises:
            ValueError: If search_type is not 'movie', 'tv', or 'multi'
        """
        if search_type not in ['movie', 'tv', 'multi']:
            raise ValueError("search_type must be 'movie', 'tv', or 'multi'")
        
        aggregated_results = {
            "query": query,
            "results": []
        }

        # 1. Collection search
        collection_result = self.get_collection_movies(query)
        if collection_result and collection_result.get("results"):
            aggregated_results["results"].extend(collection_result["results"])
        
        # 2. Keyword search
        keyword_result = self.keyword_search(query)
        if keyword_result and keyword_result.get("results"):
            aggregated_results["results"].extend(keyword_result.get("results", []))
        
        # 3. Title search
        title_search = self._make_request(f'search/{search_type}', params={"query": query, "page": page})
        if title_search and title_search.get("results"):
            aggregated_results["results"].extend(title_search.get("results", []))
        
        # Remove duplicates
        seen_ids = set()
        unique_results = []
        for item in aggregated_results["results"]:
            item_id = item.get("id")
            if item_id and item_id not in seen_ids:
                unique_results.append(item)
                seen_ids.add(item_id)
        aggregated_results["results"] = unique_results
        if aggregated_results["results"] == []:
            print(f"[WARNING]: No results found for query '{query}'.")
            aggregated_results["results"] = [{"title": "No results found", "poster_path": None, "id": 0, "media_type": "movie", "overview": "No description available.", "popularity": 0, "rating": 0, "vote_count": 0}]
        return aggregated_results
    
    def get_watch_providers(self, media_type: str, media_id: int) -> Dict:
        """
        Get streaming providers for a specific movie/show.
        
        Args:
            media_type: 'movie' or 'tv'
            media_id: TMDB ID of the content
            
        Returns:
            Dict: Streaming provider information for the content
        """
        return self._make_request(f'{media_type}/{media_id}/watch/providers')
    
    def get_content_details(self, media_type: str, media_id: int) -> Dict:
        """
        Get detailed information including rating and credits.
        
        Args:
            media_type: 'movie' or 'tv'
            media_id: TMDB ID of the content
            
        Returns:
            Dict: Detailed content information including credits
        """
        return self._make_request(f'{media_type}/{media_id}', params={"append_to_response": "credits"})
    
    def get_genre_list(self, media_type: str = 'movie') -> Dict:
        """
        Get the list of official genres for movies or TV shows.
        
        Args:
            media_type: 'movie' or 'tv'
            
        Returns:
            Dict: List of genres for the specified media type
            
        Raises:
            ValueError: If media_type is not 'movie' or 'tv'
        """
        if media_type not in ['movie', 'tv']:
            raise ValueError("media_type must be 'movie' or 'tv'")
        
        return self._make_request(f'genre/{media_type}/list')
    
    def discover_by_genre(self, media_type: str, genre_id: int, page: int = 1) -> Dict:
        """
        Discover movies or TV shows by genre.
        
        Args:
            media_type: 'movie' or 'tv'
            genre_id: The ID of the genre to filter by
            page: Page number of results to return
            
        Returns:
            Dict: Discovered content matching the genre
            
        Raises:
            ValueError: If media_type is not 'movie' or 'tv'
        """
        if media_type not in ['movie', 'tv']:
            raise ValueError("media_type must be 'movie' or 'tv'")
        
        params = {
            'with_genres': genre_id,
            'page': page,
            'sort_by': 'popularity.desc'
        }
        
        return self._make_request(f'discover/{media_type}', params=params)

    def get_provider_url(self, provider_name: str, title: str) -> str:
        """Get direct URL for streaming provider."""
        provider_info = self.PROVIDER_URLS.get(provider_name, {})
        if provider_info:
            # Use search URL with the title if available
            search_url = provider_info.get('search_url')
            if search_url:
                return search_url.format(title=title.replace(' ', '+'))
            return provider_info.get('base_url', '')
        return ''

    def process_content_item(self, item: Dict, region: str = 'NO') -> Dict:
        """Process a content item to include ratings and streaming info."""
        try:
            media_type = item.get('media_type', 'movie')
            media_id = item.get('id')
            title = item.get('title', item.get('name', ''))
            
            # Get additional details including rating
            details = self.get_content_details(media_type, media_id)
            
            # Get streaming providers with error handling
            try:
                providers = self.get_watch_providers(media_type, media_id)
                streaming_info = providers.get('results', {}).get(region, {})
            except Exception as e:
                print(f"Error fetching providers for {title}: {e}")
                streaming_info = {}
            
            # Process streaming providers with direct URLs
            def process_providers(provider_list):
                if not provider_list:
                    return []
                return [{
                    'provider_name': p.get('provider_name'),
                    'logo_path': p.get('logo_path'),
                    'provider_url': self.get_provider_url(p.get('provider_name'), title)
                } for p in provider_list if p.get('provider_name') and p.get('logo_path')]
            
            # Get both flatrate and rent providers
            flatrate_providers = process_providers(streaming_info.get('flatrate', []))
            rent_providers = process_providers(streaming_info.get('rent', []))
            
            return {
                'title': title,
                'poster_url': f"https://image.tmdb.org/t/p/w500{item.get('poster_path')}" if item.get('poster_path') else None,
                'id': media_id,
                'media_type': media_type,
                'overview': item.get('overview', 'No description available.'),
                'popularity': item.get('popularity', 0),
                'rating': details.get('vote_average', 0),
                'vote_count': details.get('vote_count', 0),
                'streaming_providers': {
                    'flatrate': flatrate_providers,
                    'rent': rent_providers,
                    'available': bool(flatrate_providers or rent_providers)
                }
            }
        except Exception as e:
            print(f"Error processing content item: {e}")
            return {
                'title': item.get('title', item.get('name', 'Unknown Title')),
                'poster_url': None,
                'id': item.get('id', 0),
                'media_type': item.get('media_type', 'unknown'),
                'overview': 'Information unavailable.',
                'popularity': 0,
                'rating': 0,
                'vote_count': 0,
                'streaming_providers': {
                    'flatrate': [],
                    'rent': [],
                    'available': False
                }
            } 