# Testing Strategy for Movie Project

This document outlines the testing strategy, types of tests employed, and specific areas of focus for ensuring the quality and reliability of the Movie Project.

## Testing Philosophy

Our primary goal with testing is to:
1.  **Ensure Correctness:** Verify that individual components and the application as a whole behave as expected.
2.  **Prevent Regressions:** Catch unintended breakages introduced by new code or modifications.
3.  **Facilitate Refactoring:** Provide a safety net when improving or changing existing code.
4.  **Serve as Documentation:** Tests often demonstrate how a piece of code is intended to be used.

We primarily focus on unit and integration tests using Django's built-in testing framework and `unittest.mock`.

## Types of Tests

### Unit Tests
Unit tests focus on the smallest testable parts of an application, isolating them from their dependencies.
-   **Purpose:** Verify the logic of individual functions, methods, or classes.
-   **Examples in this project:**
    -   `TMDBClientTests`: Tests methods of the `TMDBClient` class, mocking external HTTP requests to the TMDB API. This ensures our client correctly forms requests, handles API keys/tokens, and processes responses, without actually hitting the live API.
    -   `UserModelTests`: Tests custom methods on the `User` model, like `send_friend_request`, `accept_friend_request`, etc.
    -   `UtilityTests`: Tests helper functions in `myapp.utils` for various inputs and edge cases.
-   **Key Techniques:** Extensive use of `unittest.mock.patch` and `MagicMock` to isolate components.

### Integration Tests
Integration tests verify that different parts of the application work together correctly.
-   **Purpose:** Test interactions between components, such as views with models, templates, and utility functions, or different services.
-   **Examples in this project:**
    -   `PopularViewTest`: A comprehensive test for the `popular` view. It mocks underlying data-fetching functions (`get_popular_movies`, `get_popular_tv_shows`) and utility functions to verify:
        - Correct template usage.
        - Context variables (region, providers, watchlist, pagination objects).
        - Parameter handling (region, provider, page).
        - Data processing and sorting logic before pagination.
        - Error handling during data fetching.
        - Behavior for authenticated vs. anonymous users.
    -   `AuthTests`, `LoginViewTests`: Test the registration and login views, ensuring correct form handling, user creation, authentication state, and redirects.
    -   `WatchlistTests`: Tests the watchlist view, including authentication requirements and context data.
-   **Key Techniques:** Use of `django.test.Client` to simulate HTTP requests, assertions on response status codes, templates used, and context data. Mocking is still used to control dependencies not directly under test for a specific interaction.

## How to Run Tests

Tests can be run from the project's root directory (where `manage.py` is located):

-   **Run all tests:**
    ```bash
    python manage.py test
    ```

## Key Tested Components & Strategies

### TMDB API Client (`TMDBClient`)
-   **Strategy:** Isolate `TMDBClient` from the actual network. Mock `requests.get` and environment variables (`TMDB_API_KEY`, `TMDB_ACCESS_TOKEN`).
-   **Coverage:**
    -   Initialization logic (handling API keys/tokens).
    -   Correct formation of API request URLs and parameters for various endpoints (`get_popular_movies`, `search`, etc.).
    -   Correct handling and parsing of mocked JSON responses.
    -   Error handling for missing API keys.
    -   Specific methods like `get_provider_url` and `process_content_item`.
-   **Example:** `TMDBClientTests`.

### Views
-   **Strategy:** Use `django.test.Client` to make requests. Mock service functions or utility functions that views call to control inputs and isolate view logic.
-   **Coverage:**
    -   Response status codes (200, 302, 404, etc.).
    -   Templates used.
    -   Context data passed to templates (e.g., `page_obj`, `selected_region`, `watchlist_ids`).
    -   Handling of GET/POST parameters.
    -   Authentication and authorization checks.
    -   Form processing (for views with forms).
    -   Error handling within the view.
-   **Example:** `PopularViewTest`, `IndexViewTest`, `AuthTests`, `LoginViewTests`, `WatchlistTests`.

### Models
-   **Strategy:** Test custom model methods directly. Verify model constraints (e.g., `unique_together`) by attempting to create data that violates them (expecting `IntegrityError`).
-   **Coverage:**
    -   Custom methods on models (e.g., `User.get_friends()`, `User.send_friend_request()`).
    -   Model creation and field validation (implicitly tested by ORM, but custom validation could be added).
    -   Relationships and their impact.
-   **Example:** `UserModelTests`, `WatchedMovieTests`, `BadgeSystemTests`.

### Authentication System
-   **Strategy:** Test login, registration, and logout flows using `django.test.Client`. Verify user authentication state.
-   **Coverage:**
    -   Successful and failed login attempts.
    -   Successful registration and user creation.
    -   Redirection logic post-authentication.
    -   Access control for views requiring login.
-   **Example:** `AuthTests`, `LoginViewTests`. `setUp` methods often include `SocialApp` and `Site` creation for `allauth` compatibility.

### Utility Functions
-   **Strategy:** Test utility functions in `myapp/utils.py` with a range of valid and invalid inputs to ensure they behave correctly under various conditions.
-   **Coverage:**
    -   `get_provider_logo_url`: Handling of different path formats, None values.
    -   `encode_filters_for_pagination`: Correctly building query strings.
    -   `paginate_results`: Handling valid page numbers, invalid page numbers (strings, out of range).
    -   `_extract_providers_for_item`: Correctly parsing provider data from mock content items.
    -   `process_content_item`: Correctly transforming raw content data into a dictionary suitable for templates.
    -   `get_validated_region`, `get_poster_url`.
-   **Example:** `UtilityTests`.

### Understanding Search API Responses (Exploratory Testing)
To effectively implement and test search functionality that relies on the TMDB API, it's crucial to understand the structure of the JSON responses returned by different search endpoints. The following details were gathered through exploratory testing/API inspection:

#### Collection Search
The `/search/collection` endpoint returns collection metadata. To get individual movies within a collection, you typically need to use the collection's `id` to call the `/collection/{collection_id}` endpoint. The `parts` key in the collection detail response contains the list of movies.

*Sample Collection Detail JSON (after fetching by collection ID):*
```json
{
  "id": 10,
  "name": "Star Wars Collection",
  "overview": "An epic space-opera theatrical film series...",
  "poster_path": "/bYbHqvRANCpu6bSSnfe4VxL2s7g.jpg",
  "backdrop_path": "/d8duYyyC9J5T825Hg7grmaabfxQ.jpg",
  "parts": [
    {
      "id": 11,
      "title": "Star Wars: Episode IV - A New Hope",
      "release_date": "1977-05-25",
      "poster_path": "/path.jpg"
      // ... Other movie details
    },
    {
      "id": 1891,
      "title": "Star Wars: Episode V - The Empire Strikes Back"
      // ... Other movie details
    }
    // and so on
  ]
}