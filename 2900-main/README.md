# INF-2900: Movie Discovery Platform

A web application built with Django that helps users discover movies and TV shows through an intuitive search interface and a unique randomizer wheel feature.  
The platform integrates with TMDB (The Movie Database) API to provide up-to-date content.

## Navigation
- [Project Structure](#-project-structure)
- [Core Features](#-core-features)
- [Technology Stack](#-technology-stack)
- [API KEY & TMDB Access Token](#api_key-tmdbapi-read-access-token)
- [How to run](#how-to-run)

# 📂 Project Structure 
```
2900/
├── Docs/
├── Illustrations/
├── site/
│   ├── media/
│   │   ├── posters/
│   │   └── providers/
│   ├── myapp/
│   │   ├── management/
│   │   │   └── commands/           # Contains scripts from the TMDB API to collect data and populate DBs. 
│   │   ├── migrations/
│   │   ├── css/   
│   │   │   └── **.css                 
│   │   ├── images/                 # Contains images for backgrounds and such
│   │   │   ├── **.png
│   │   │   └── **.jpg
│   │   ├── js/                     # Contains JavaScript files
│   │   │   ├── randomizer.js
│   │   │   ├── script.js
│   │   │   └── sidebar.js
│   │   ├──templates/
│   │   │   └── **.html             # Contains all HTML files
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── context_processors.py
│   │   ├── models.py
│   │   ├── populate_db.py
│   │   ├── tests.py                # This file contains all test functions
│   │   ├── tmdb_client.py          # This file contains most of the logic that interacts with the TMDB API 
│   │   ├── urls.py
│   │   ├── utils.py
│   │   └── views.py
│   └── project_movie/
│       ├── asgi.py
│       ├── settings.py
│       ├── urls.py
│       └── wsgi.py
├── .gitingore
├── README.md
├── Requirements.txt            # Contains all requirements for the project
└── setup.py
```

# 🎯 Core Features

- **Movie & TV Show Search**
  - Real-time search functionality
  - Comprehensive results with movie posters
  - Detailed information including titles and descriptions
  - Clean, user-friendly results display

- **Randomizer Wheel**
  - Interactive spinning wheel for content discovery
  - Three filtering options:
  - All Content
  - Movies Only
  - TV Shows Only
  - Smooth spinning animation
  - Visual result display with movie/show poster

- **Modern Interface**
  - Dark theme for better viewing experience
  - Responsive design for all devices
  - Fixed header with navigation
  - Hamburger menu for mobile
  - Clean, minimal footer

# 🛠 Technology Stack

- **Backend**
  - Django (Python web framework)
  - TMDB API integration
  - JSON response handling
  - RESTful endpoints

- **Frontend**
  - Vanilla JavaScript 
  - CSS
  - HTML5
  - Dynamic DOM manipulation



# How to run
## **Setup & Activate a Virtual Environment**
  ```Bash
  python -m venv venv
  ```
  
### Mac/linux:  
```Bash
source venv/bin/activate
```
  
### Windows:  
```Bash
source venv\Scripts\activate
```
  
```cmd
call venv\Scripts\activate
```
# API_KEY TMDB/API Read Access Token:
- This project requires a TMDB API Key and an API Read Access Token.
- The API access key and token should be provided in the .env file, if not follow the instructions below.
1. Register user:
- https://www.themoviedb.org/
2. Get api key:
- Install python-dotenv via terminal (make sure you are in venv):
- pip install python-dotenv
- The api key/API Read Access Token is found: "https://www.themoviedb.org/settings/api"
3.  Make a ".env" file, and write:
- TMDB_API_KEY=your_actual_api_key_here
- TMDB_ACCESS_TOKEN=your_actual_read_access_token_here
  
**from directory 2900, run:**
```Bash
python setup.py
```
**Navigate to correct directory:** 
```Bash
cd site
```
**run the server:**
```Bash
python manage.py runserver
```
Open your web browser and go to:
http://127.0.0.1:8000/

## **The setup script will:**
* Install dependencies from `requirements.txt`.
* Create/ensure the `.env` file exists in `site/`.
* Run Django database migrations (`makemigrations` if fresh start, then `migrate`).
* Run custom management commands:
  * `create_initial_badges`: Sets up predefined achievement badges.
  * `createcachetable`: Sets up Django's database caching.
  * `collectstatic`: Gathers static files.
  * `populate_db`: Fetches popular movies & TV shows.
  * `populate_genres`: Fetches genre information.
  * `update_details`: Fetches more detailed info for existing content.
  * `update_watch_providers`: Fetches streaming provider info.
  * `get_providers_logo`: Downloads logos for streaming providers.
* Run tests.
* Note! the .env file does not generate with values for API_KEY and ACCESS_TOKEN.
