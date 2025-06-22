from django.core.management.base import BaseCommand
import subprocess
import sys

class Command(BaseCommand):
    help = 'Runs all database setup and population commands'

    def handle(self, *args, **options):
        def run_command(command):
            try:
                subprocess.run(command, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                self.stdout.write(self.style.ERROR(f"Error running command '{command}': {str(e)}"))
                sys.exit(1)

        # Define command sets
        fresh_start_commands = [
            "rm db.sqlite3",
            "rm myapp/migrations/0*.py",
            "python manage.py makemigrations",
            "python manage.py migrate",
            "python manage.py populate_db",
            "python manage.py populate_genres",
            "python manage.py update_details --media-type both --force",
            "python manage.py update_watch_providers --media-type both",
            "python manage.py get_providers_logo",
            "python manage.py createcachetable",
            "python manage.py create_initial_badges",
            "python manage.py collectstatic --noinput",
            "python manage.py test",
            "python manage.py runserver"
        ]

        keep_db_commands = [
            "python manage.py populate_db",
            "python manage.py populate_genres",
            "python manage.py update_details --media-type both --force",
            "python manage.py update_watch_providers --media-type both",
            "python manage.py get_providers_logo",
            "python manage.py createcachetable",
            "python manage.py test",
            "python manage.py runserver"
        ]

        # Show options
        self.stdout.write(self.style.SUCCESS(
            "\nChoose setup option:\n"
            "1. Fresh start (delete everything and start fresh)\n"
            "2. Keep database (update existing database)\n"
            "3. Cancel\n"
        ))

        while True:
            choice = input("Enter your choice (1/2/3): ").strip()
            if choice in ['1', '2', '3']:
                break
            self.stdout.write(self.style.ERROR("Please enter 1, 2, or 3"))

        if choice == '3':
            self.stdout.write(self.style.SUCCESS("Operation cancelled."))
            return

        # Set commands and warning message based on choice
        if choice == '1':
            commands = fresh_start_commands
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
            commands = keep_db_commands
            warning_message = (
                "\n⚠️  WARNING ⚠️\n"
                "This will:\n"
                "1. Update existing database with fresh data\n"
                "2. Run all setup commands\n\n"
                "Existing data will be updated or supplemented!\n"
            )

        # Show warning and get confirmation
        self.stdout.write(self.style.WARNING(warning_message))

        while True:
            user_input = input("Are you sure you want to continue? (yes/no): ").lower()
            if user_input in ['yes', 'no']:
                break
            self.stdout.write(self.style.ERROR("Please answer 'yes' or 'no'"))

        if user_input == 'no':
            self.stdout.write(self.style.SUCCESS("Operation cancelled."))
            return

        # Execute commands
        self.stdout.write(self.style.SUCCESS("\nStarting setup process..."))
        
        for command in commands:
            self.stdout.write(self.style.SUCCESS(f"\nExecuting: {command}"))
            try:
                run_command(command)
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"\nAn error occurred during setup: {str(e)}\n"
                    "Setup process was not completed successfully."
                ))
                return

        self.stdout.write(self.style.SUCCESS(
            "\n✅ Setup completed successfully!\n"
            "The development server is now running."
        ))