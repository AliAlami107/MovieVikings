# MovieVikings Views Documentation

This document outlines the core views within the Movievikings application, detailing their functionality, URL patterns, and usage.

## Core & Static Pages

-   **`index`**
    -   **URL Pattern:** `''` (Root path)
    -   **URL Name:** `index`
    -   **Purpose:** Renders the homepage.
    -   **Auth:** None


-   **`contact`**
    -   **URL Pattern:** `contact/`
    -   **URL Name:** `contact`
    -   **Purpose:** Displays contact form.
    -   **Auth:** None

-   **`privacy`**
    -   **URL Pattern:** `privacy/`
    -   **URL Name:** `privacy`
    -   **Purpose:** Displays privacy policy.
    -   **Auth:** None

-   **`about`**
    -   **URL Pattern:** `about/`
    -   **URL Name:** `about`
    -   **Purpose:** Displays about page.
    -   **Auth:** None

## Content Discovery & Display

-   **`search`**
    -   **URL Pattern:** `search/`
    -   **URL Name:** `search`
    -   **Purpose:** Handles TMDB search for movies/TV based on `query` and `region` (GET params). Results usually displayed on `index.html` or a dedicated results page.
    -   **Auth:** None (Watchlist status enhanced if logged in)

-   **`popular`**
    -   **URL Pattern:** `popular/`
    -   **URL Name:** `popular`
    -   **Purpose:** Displays paginated popular movies/TV, filterable by `region`, `provider`, `page` (GET params).
    -   **Auth:** None (Watchlist status enhanced if logged in)

-   **`randomizer`**
    -   **URL Pattern:** `randomizer/`
    -   **URL Name:** `randomizer`
    -   **Purpose:** Renders the random content discovery page. Content fetched via `get_random_content` API.
    -   **Auth:** None

-   **`get_random_content` (API)**
    -   **URL Pattern:** `randomizer/get-random-content/`
    -   **URL Name:** `get_random_content`
    -   **Purpose:** JSON API for fetching random content for the wheel, filterable by `region` and `genre` (GET params).
    -   **Auth:** None

-   **`trending`**
    -   **URL Pattern:** `trending/`
    -   **URL Name:** `trending`
    -   **Purpose:** Displays top 10 trending movies/TV. `region` (GET param) for streaming info.
    -   **Auth:** None (Watchlist status enhanced if logged in)

-   **`content_detail`**
    -   **URL Pattern:** `<str:media_type>/<int:media_id>/`
    -   **URL Name:** `content_detail`
    -   **Purpose:** Detailed page for a movie or TV show. `region` (GET param) for streaming info.
    -   **Auth:** None (Watchlist status enhanced if logged in)

-   **`actor_detail`**
    -   **URL Pattern:** `actor/<str:actor_name>/`
    -   **URL Name:** `actor_detail`
    -   **Purpose:** Actor's biography and filmography.
    -   **Auth:** None

-   **`director_detail`**
    -   **URL Pattern:** `director/<str:director_name>/`
    -   **URL Name:** `director_detail`
    -   **Purpose:** Director's biography and filmography.
    -   **Auth:** None

## User Authentication & Account

-   **`login_view`**
    -   **URL Pattern:** `login/`
    -   **URL Name:** `login`
    -   **Purpose:** Handles user login (POST: `username`, `password`).
    -   **Auth:** None

-   **`logout` (Django built-in)**
    -   **URL Pattern:** `logout/`
    -   **URL Name:** `logout`
    -   **Purpose:** Logs out the current user.
    -   **Auth:** Required (to be logged in)

-   **`register_view`** (Custom)
    -   **URL Pattern:** `register/`
    -   **URL Name:** `register`
    -   **Purpose:** Custom user registration (POST: `username`, `email`, `password1`, `password2`).
    -   **Auth:** None

-   **`delete_account_view`**
    -   **URL Pattern:** `settings/delete-account/`
    -   **URL Name:** `delete_account`
    -   **Purpose:** Allows logged-in user to delete their account (POST: `password`).
    -   **Auth:** Required

-   **`change_password_view`**
    -   **URL Pattern:** `settings/change-password/`
    -   **URL Name:** `change_password`
    -   **Purpose:** Allows logged-in user to change password (POST: `old_password`, `new_password1`, `new_password2`).
    -   **Auth:** Required

## User Profile & Social Features

-   **`profile_view`**
    -   **URL Pattern:** `profile/`
    -   **URL Name:** `profile`
    -   **Purpose:** User dashboard (stats, badges, recent activity). Handles POST actions like mark as watched, rate, remove from lists. GET params: `show`, `page`.
    -   **Auth:** Required

-   **`watchlist`**
    -   **URL Pattern:** `watchlist/`
    -   **URL Name:** `watchlist`
    -   **Purpose:** Displays user's watchlist.
    -   **Auth:** Required

-   **`add_to_watchlist` (API)**
    -   **URL Pattern:** `watchlist/add/<str:media_type>/<int:media_id>/`  *(Note: Assumed `media_id` is int)*
    -   **URL Name:** `add_to_watchlist`
    -   **Purpose:** Adds/Removes item from watchlist (toggles). POST params: `title`, `poster_path`. Returns JSON.
    -   **Auth:** Required

-   **`remove_from_watchlist` (API)**
    -   **URL Pattern:** `watchlist/remove/<str:media_type>/<int:media_id>/` *(Note: Assumed `media_id` is int)*
    -   **URL Name:** `remove_from_watchlist`
    -   **Purpose:** Removes item from watchlist. Returns JSON.
    -   **Auth:** Required

-   **`my_available_content`**
    -   **URL Pattern:** `my_available_content/`
    -   **URL Name:** `my_available_content`
    -   **Purpose:** (Placeholder) To show content on user's selected streaming services.
    -   **Auth:** Required

-   **`settings_view`**
    -   **URL Pattern:** `settings/`
    -   **URL Name:** `settings`
    -   **Purpose:** (Placeholder / Not in Use) User settings, e.g., streaming service preferences.
    -   **Auth:** Required

-   **`send_friend_request_view`**
    -   **URL Pattern:** `friends/send-request/`
    -   **URL Name:** `send_friend_request`
    -   **Purpose:** Sends a friend request (POST: `username`). (Action likely submitted from profile page)
    -   **Auth:** Required

-   **`accept_friend_request_view`**
    -   **URL Pattern:** `friends/accept-request/<int:request_id>/`
    -   **URL Name:** `accept_friend_request`
    -   **Purpose:** Accepts a friend request.
    -   **Auth:** Required

-   **`reject_friend_request_view`**
    -   **URL Pattern:** `friends/reject-request/<int:request_id>/`
    -   **URL Name:** `reject_friend_request`
    -   **Purpose:** Rejects a friend request.
    -   **Auth:** Required

-   **`unfriend_view`**
    -   **URL Pattern:** `friends/unfriend/`
    -   **URL Name:** `unfriend`
    -   **Purpose:** Removes a friend (POST: `username`). (Action likely submitted from profile page)
    -   **Auth:** Required

-   **`my_friend_view`**
    -   **URL Pattern:** `friend/<str:username>/`
    -   **URL Name:** `my_friend`
    -   **Purpose:** Displays a friend's public profile and stats.
    -   **Auth:** Required

## Custom Error Handlers

-   **`handler404`**: Custom 404 error page (configured in root `urls.py`).
-   **`handler500`**: Custom 500 error page (configured in root `urls.py`).

## Internal Helper Functions

-   **`get_watchlist_ids(user)`**: Utility to fetch media IDs from a user's watchlist. Used internally by other views, not a URL endpoint.