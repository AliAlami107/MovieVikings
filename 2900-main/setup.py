#!/usr/bin/env python
"""
Setup script for the Movie Project
This script sets up the necessary environment for running the Movie Project.
It handles database migrations, creating necessary tables, and populating data.
Works on both Windows and Linux.
"""

# Standard library imports for file operations, subprocess handling, and platform detection
import os
import sys
import subprocess
import platform

# Define absolute paths to ensure consistent file access regardless of where the script is executed from
# This helps prevent "file not found" errors when running commands or accessing files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get the absolute path to the project root directory
SITE_DIR = os.path.join(BASE_DIR, "site")  # Path to the Django site directory

# Terminal colors class for prettier output
# Colors are only used on non-Windows platforms, otherwise empty strings are used
class Colors:
    GREEN = '\033[0;32m' if platform.system() != 'Windows' else ''
    YELLOW = '\033[1;33m' if platform.system() != 'Windows' else ''
    RED = '\033[0;31m' if platform.system() != 'Windows' else ''
    NC = '\033[0m' if platform.system() != 'Windows' else ''  # No Color (reset)

def print_colored(message, color):
    """
    Print colored text if supported by the platform
    Args:
        message: The text to print
        color: The color code to use
    """
    print(f"{color}{message}{Colors.NC}")

def run_command(command, cwd=None):
    """
    Run a shell command and handle errors
    
    Args:
        command: The command to execute
        cwd: The directory to run the command in (working directory)
        
    Returns:
        True if the command was successful, False otherwise
    """
    try:
        print_colored(f"Running: {command}", Colors.YELLOW)
        # Use subprocess.run with check=True to raise an exception if the command fails
        # cwd parameter sets the working directory for the command execution
        subprocess.run(command, shell=True, check=True, cwd=cwd)
        return True
    except subprocess.CalledProcessError as e:
        # This exception is raised when the process returns a non-zero exit code
        print_colored(f"Error running command '{command}': {str(e)}", Colors.RED)
        return False
    except Exception as e:
        # Catch any other exceptions that might occur
        print_colored(f"Unexpected error: {str(e)}", Colors.RED)
        return False

def create_env_file():
    """
    Create .env file if it doesn't exist
    
    The .env file stores environment variables like API keys
    that shouldn't be committed to version control
    
    Returns:
        True if the file exists or was created successfully, False otherwise
    """
    env_file_path = os.path.join(SITE_DIR, ".env")
    if not os.path.exists(env_file_path):
        print_colored("Creating .env file...", Colors.YELLOW)
        # Template content for the .env file
        env_content = """# TMDB API credentials
                    # You need to set at least one of these
                    TMDB_API_KEY=your_api_key_here
                    TMDB_ACCESS_TOKEN=your_access_token_here
                    """
        try:
            with open(env_file_path, "w") as f:
                f.write(env_content)
            print_colored("Created .env file. Please edit it to add your TMDB API keys.", Colors.GREEN)
        except Exception as e:
            print_colored(f"Failed to create .env file: {str(e)}", Colors.RED)
            return False
    else:
        print_colored(".env file already exists.", Colors.GREEN)
    return True

def install_dependencies():
    """
    Install dependencies from requirements.txt
    
    Returns:
        True if dependencies were installed successfully, False otherwise
    """
    print_colored("Installing dependencies...", Colors.YELLOW)
    if not run_command("pip install -r requirements.txt", cwd=BASE_DIR):
        print_colored("Failed to install dependencies.", Colors.RED)
        return False
    return True

def setup_database():
    """
    Run database migrations and setup necessary tables
    
    This function:
    1. Creates the .env file if it doesn't exist
    2. Runs database migrations
    3. Creates initial badges
    4. Sets up cache tables
    5. Collects static files
    
    Returns:
        True if all operations were successful, False otherwise
    """
    # Create .env file
    if not create_env_file():
        return False
    
    # Run migrations
    if not run_command("python manage.py migrate", cwd=SITE_DIR):
        print_colored("Failed to run migrations.", Colors.RED)
        return False
    
    # Create initial badges
    if not run_command("python manage.py create_initial_badges", cwd=SITE_DIR):
        print_colored("Failed to create initial badges.", Colors.RED)
        return False
    
    # Create cache table
    if not run_command("python manage.py createcachetable", cwd=SITE_DIR):
        print_colored("Failed to create cache table.", Colors.RED)
        return False
    
    # Collect static files
    if not run_command("python manage.py collectstatic --noinput", cwd=SITE_DIR):
        print_colored("Failed to collect static files.", Colors.RED)
        return False
    
    return True

def populate_data():
    """
    Populate database with movies, TV shows, genres, and other data
    
    This function runs multiple Django management commands to fetch
    and populate the database with data from external APIs.
    
    Returns:
        True once all commands have been attempted (even if some fail)
    """
    # Populate database with movies and TV shows
    print_colored("Populating database with movies and TV shows...", Colors.YELLOW)
    print_colored("This may take a few minutes...", Colors.YELLOW)
    
    # Each command is run separately to handle errors individually
    # If one command fails, we still try to run the others
    commands = [
        "python manage.py populate_db --media-type=both --pages=3",  # Populate movies and TV shows
        "python manage.py populate_genres",                          # Add genres
        "python manage.py update_details --media-type both",         # Update movie and TV show details
        "python manage.py update_watch_providers --media-type both", # Add streaming provider information
        "python manage.py get_providers_logo"                        # Download provider logos
    ]
    
    for command in commands:
        if not run_command(command, cwd=SITE_DIR):
            print_colored(f"Failed to run: {command}", Colors.RED)
            print_colored("You can manually run this later.", Colors.YELLOW)
            # Continue with other commands even if one fails
    
    return True

def main():
    """
    Main function to run the setup
    
    This function:
    1. Presents setup options to the user
    2. Confirms the user's choice
    3. Installs dependencies
    4. Performs the chosen setup actions
    5. Sets up the database
    6. Populates the database with data
    7. Runs tests
    """
    print_colored("Setting up the Movie Project...", Colors.GREEN)
    
    # Get user choice for setup - interactive menu
    print_colored(
        "\nChoose setup option:\n"
        "1. Fresh start (delete everything and start fresh)\n"
        "2. Keep database (update existing database)\n"
        "3. Cancel\n",
        Colors.GREEN
    )
    
    # Input validation loop
    choice = ""
    while choice not in ['1', '2', '3']:
        choice = input("Enter your choice (1/2/3): ").strip()
        if choice not in ['1', '2', '3']:
            print_colored("Please enter 1, 2, or 3", Colors.RED)
    
    # Early exit if user chooses to cancel
    if choice == '3':
        print_colored("Operation cancelled.", Colors.GREEN)
        return
    
    # Set warning message based on choice
    if choice == '1':
        # Fresh start warning
        warning_message = (
            "\n⚠️  WARNING ⚠️\n"
            "This will:\n"
            "1. Delete your existing database (db.sqlite3)\n"
            "2. Delete all existing migrations\n"
            "3. Create new migrations and database\n"
            "4. Populate the database with fresh data\n"
            "5. Run all setup commands\n\n"
            "All existing data will be lost!\n"
        )
    else:  # choice == '2'
        # Update warning
        warning_message = (
            "\n⚠️  WARNING ⚠️\n"
            "This will:\n"
            "1. Update existing database with fresh data\n"
            "2. Run all setup commands\n\n"
            "Existing data will be updated or supplemented!\n"
        )
    
    # Show the warning and get confirmation
    print_colored(warning_message, Colors.YELLOW)
    
    # Confirmation input validation loop
    user_input = ""
    while user_input not in ['yes', 'no']:
        user_input = input("Are you sure you want to continue? (yes/no): ").lower()
        if user_input not in ['yes', 'no']:
            print_colored("Please answer 'yes' or 'no'", Colors.RED)
    
    # Early exit if user decides not to continue
    if user_input == 'no':
        print_colored("Operation cancelled.", Colors.GREEN)
        return
    
    # Install dependencies first, as they're required for everything else
    if not install_dependencies():
        sys.exit(1)
    
    # Fresh start option - delete database and migrations
    if choice == '1':
        # Remove existing database file
        db_path = os.path.join(SITE_DIR, "db.sqlite3")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print_colored("Removed existing database.", Colors.GREEN)
            except Exception as e:
                print_colored(f"Failed to remove database: {str(e)}", Colors.RED)
                sys.exit(1)
        
        # Remove existing migration files (Django keeps track of applied migrations in these files)
        import glob
        migration_pattern = os.path.join(SITE_DIR, "myapp/migrations/0*.py")
        for migration_file in glob.glob(migration_pattern):
            try:
                os.remove(migration_file)
                print_colored(f"Removed migration file: {migration_file}", Colors.GREEN)
            except Exception as e:
                print_colored(f"Failed to remove migration file {migration_file}: {str(e)}", Colors.RED)
        
        # Create new migrations
        if not run_command("python manage.py makemigrations", cwd=SITE_DIR):
            print_colored("Failed to create migrations.", Colors.RED)
            sys.exit(1)
    
    # Setup database (migrations, badges, cache table, static files)
    if not setup_database():
        sys.exit(1)
    
    # Populate data (movies, TV shows, genres, providers)
    if not populate_data():
        # Continue even if population fails
        # Some population commands might fail but the application can still run
        pass
    
    # Run tests to verify the setup
    if not run_command("python manage.py test", cwd=SITE_DIR):
        print_colored("Some tests failed. You may want to investigate.", Colors.YELLOW)
    
    # Show completion message and next steps
    print_colored(
        "\n================================================================",
        Colors.GREEN
    )
    print_colored("Setup complete! To run the application:", Colors.GREEN)
    print_colored("Don't forget to edit the .env file with your TMDB API credentials.", Colors.YELLOW)
    print("")
    print("  1. Go to the site directory:")
    print("     cd site")
    print("")
    print("  2. Start the server:")
    print("     python manage.py runserver")
    print_colored(
        "================================================================",
        Colors.GREEN
    )

# Script entry point
if __name__ == "__main__":
    main() 