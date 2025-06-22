### 1 populate_db
**Purpose:**
Fetches initial popular movie and TV show data from TMDB to populate the Movie and TVShow tables. This script gets the foundational content into the system.

**Key Actions:**

* Retrieves lists of popular movies and/or TV shows.

* Creates or updates Movie or TVShow records with basic info (tmdb_id, title, overview, poster_path, popularity, rating, release_date, etc.).

* Associates content with Genre objects (creates genres if they don't exist based on TMDB IDs).

* Attempts to download poster images locally to media/posters/ and updates poster_path.

**Command:**

```Bash
python manage.py populate_db [options]
```
**Options:**

* --media-type <movie|tv|both>: Specifies media type to fetch. (Default: both)

* --pages <number>: Number of pages of results to fetch per media type. (Default: 5)

### 2 populate_genres
**Purpose:**
Fetches the complete list of official movie and TV show genres from TMDB and stores them in the Genre table.

**Key Actions:**

* Retrieves genre lists from TMDB.

* Creates or updates Genre records with tmdb_id and name.

**Command:**

```Bash
python manage.py populate_genres
```
### 3 update_details
**Purpose:**
Fetches detailed information for movies and TV shows already in the database, enriching them with runtime, crew, and more.

**Key Actions:**

* Iterates through existing Movie and TVShow records.

* Fetches full details from TMDB for each.

* Updates records with runtime, number of seasons, full genre objects, and more.

**Command:**

```Bash
python manage.py update_details --media-type <movie|tv|both>
```
**Options:**

* --media-type <movie|tv|both>: Specifies what content to update.

### 4 update_watch_providers
**Purpose:**
Fetches and stores streaming, rental, and purchase availability for movies and TV shows across regions.

**Key Actions:**

* Iterates through existing Movie and TVShow records.

* Fetches watch provider data from TMDB.

* Creates/updates StreamingProvider records.

* Links content to providers by region and offer type.

**Command:**

```Bash
python manage.py update_watch_providers --media-type <movie|tv|both>
```
**Options:**

* --media-type <movie|tv|both>: Specifies what content to update.

### 5 get_providers_logo
Purpose:
Downloads logo images for streaming providers stored in the StreamingProvider table.

**Key Actions:**

* Iterates through StreamingProvider records.

* Downloads logos from TMDB based on logo_path.

* Saves images locally to media/provider_logos/.

* Updates StreamingProvider.logo_path with the local path.

**Command:**

```Bash
python manage.py get_providers_logo
```
### 6 create_initial_badges
**Purpose:**
Populates the Badge table with a predefined set of achievement badges users can earn.

**Key Actions:**

* Checks for existing badges to avoid duplicates.

* Creates Badge records with: name, description, badge_type, rarity, icon,requirement_count, requirement_type
**Command:**
```Bash
python manage.py create_initial_badges
```