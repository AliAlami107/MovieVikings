
# INF-2900 Meeting logs and Sprint log written on our meetings
**Also including retrospectives and progress**

## First meeting (29. April)
Not all team members had been introduced to each other, so we spent some time getting to know each other. Each team member came up with ideas for potential web applications, and through anonymous voting, we selected the concept of a platform that allows users to search up their favorite movies and TV-shows and see what streaming services offer them. 
We planned to meet at least once a week either physically or though Discord calls. We chose to follow a scrum framework where sprints will last for one week and we would rotate on different roles. 

----------------------------------------------------------------------------------------------------------------

## Sprint 1(6. February -> 13. February)
Scrum Master: Ali 
### Work completed:  
- Set up Django project and had made initial directory structure
- Added files: 
- .gitignore
- Django views, app, models and test files 
- TMDB integration 
- Template folder for the front-end structure
### Sprint Goals:
- Develop the initial UI structure, including: 
- Search bar 
- Navigation elements 
- Buttons for trending and popular movies
- Create homepage with header and footer

### Progress Summary
- We have set up the project foundation
- All team members can push and pull to github to make a synchronized development envinroment 

### Retrospective 
- Quick team setup
- Increase sprint time from 1 weak to 2 weaks after Ali has finished his 2 weaks

----------------------------------------------------------------------------------------------------------------

## Sprint 2(13. February -> 20. February)
Scrum Master: Ali
### Work completed: 
- Implemented header, footer and search bar 
### Goal for this sprint: 
- Finish frontpage on the frontend part
- Add tests 
- Improve HTML structure
### Progress Summary
- Frontend components implemented as planned 
- Layout looks good
- Not so mush work done this sprint  

### Retrospective 
- Solid UI progress 
- TA tells us we are a bit behind other groups
- Add more tests for next sprint 
- Balance frontend and backend tasks better 


----------------------------------------------------------------------------------------------------------------

## Sprint 3(20. February -> 6. March)
Scrum Master: Henrik 
### Work completed: 
- Integrated TMDB API for retrieving movie data
- Improved movie/TV show models for database storage
- Registered key API endpoints
- Implemented some error handling for streaming provider data
- Added poster image support and refined display logic
- Conducted basic testing with unit test setup
- Improved HTML structure with a base.html and removed redundant code
- Updated site branding with logo and background image
- Cleanup
### Goal for this sprint: 
- Implement user registration and authentication 
- Implement watchlist and movie detail page
- Improve streaming provider display 
- Start on “FOR U” and rating features

### Progress Summary
- API and models are working nicely 
- preperations for user features are underway 

### Retrospective 
- Ask users what they want from the application 
- Find a solution for merging conflicts

----------------------------------------------------------------------------------------------------------------

## Sprint 4(6. March -> 20. March)
Scrum Master: Audun 
### Work completed: 
- Added user registration and login with local database
- Started on Google authentication
- Implemented and styled a watchlist 
- Implemented movie detail pages with data fetched from API
- Added profile and footer endpoints
- Normalized streaming provider data and displayed logos in search -results
- Set up sidebar component and basic layout structure
- More error handling and cleanup 
- Added UML diagram and updated README
- Added buttons and minor UI components for navigation and content interaction
- Started on “FOR U” and rating system 

### Goal for this sprint: 
- Add some functionality for watched media and user rating
- Improve user profile 
- Add remove options for better user experience
- Refine UI navigation and error handling

### Progress Summary
- Some problems with google authentication 
- Team still works great together 

### Retrospective 
- Find out if we should have google authentication, might be to complicated for now

----------------------------------------------------------------------------------------------------------------

## Sprint 5 (20. March -> 3. April)
Scrum Master: Lars Daniel 
### Work completed: 
- Implemented watched media functionality with user ratings on profile page
- Added 404 and 500 error pages
- Introduced movie counter and watch tracker on the profile page
- Added remove buttons for watched items and watchlist entries
- Updated logout behavior and profile navigation
- Made minor improvements to settings and available content templates

### Goal for this sprint: 
- Implement friends and challenges for users 
- Polish UI and improve settings
- Add region filtering 
- Refactor code for better readability and maintainability 

### Progress Summary
- Productive sprint
- Decided to not have google authentication 
- Struggling a bit with the speed of the application

### Retrospective 
- Find out how to fix speed 
- Decide how final product should look like 

----------------------------------------------------------------------------------------------------------------

## Sprint 6 (3. April -> 17. April)
Scrum Master: Ali
### Work completed: 
- Implemented friend system with add/remove functionality and dedicated friend page
- Enabled account removal and improved settings page layout
- Styled the app with updated logo, background, and UI improvements
- Improved filtering for providers and cleaned up HTML structure
- Added text review feature 
- Enhanced popular content to be region-based and fixed pagination logic
- Split HTML files and organized view logic for better readability
- General bug fixes and interface polish

### Goal for this sprint: 
- Improve randomizer 
- Improve the search function and backend testing 
- Improve my profile 
- Cleanup backend 

### Progress Summary
- Decided how our finished product should look and what functionalities we should have. 
- Would like to be done with the code part soon so that we can focus on report, testing, and polish .
- Easter break so no meeting on the 17.April 

### Retrospective 
- Expand some of the elements of our already working functions
- We should have planned how we moved on to the next sprint in the middle of easter

----------------------------------------------------------------------------------------------------------------

## Sprint 7 (17. April -> 1. May)
Scrum Master: Henrik 
### Work completed: 
- Randomizer wheel improved, now supports genre selection
- Implemented challenges feature and enabled viewing of friend badges
- Updated database drawing and improved migration documentation in HOWTO.md
- Improved search functionality and merged fix for test search
- Added testing support including new test files and templates
- Implemented and debugged pycache tracking logic
- Cleaned up .gitignore and removed unnecessary database files

### Goal for this sprint: 
- Improve randomizer 
- Improve the search function and backend testing 
- Improve my profile 
- Cleanup backend

### Progress Summary
- All elements of our implementation is working or is close to working as they should
- Team is working good

### Retrospective 
- The last two weeks are only report, testing and polishing 

----------------------------------------------------------------------------------------------------------------

## Sprint 8 (1. May -> 15. May)
Scrum Master: Audun
### Work completed: 
- Finished director and actor pages, including initial frontend and data integration
- Added build script and example .env file for API key configuration
- Wrote and ran tests for popular content
- Updated .gitignore to exclude unnecessary files and database artifacts
- Updated DB drawing
- Merged and finalized changes for popular content display
- Continued frontend refinements, including styling and UI adjustments

### Goal for this sprint: 
- Final touches 

### Progress Summary
- We have achived our goal, however we would like to have more time, because we have a lot more ideas to make the application better 




