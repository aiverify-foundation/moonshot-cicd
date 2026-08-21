import toml

# Load metadata from pyproject.toml
with open("pyproject.toml", "r") as f:
    pyproject = toml.load(f)

_project = pyproject["project"]
_author = _project["authors"][0]
app_name = _project["name"]
__version__ = _project["version"]
__author__ = (
    f"{_author['name']} <{_author['email']}>"
    if _author.get("email")
    else _author["name"]
)
__license__ = _project["license"]
__description__ = _project["description"]


def welcome() -> None:
    """
    Display Project Moonshot logo
    """
    logo = "  _____           _           _     __  __                       _           _   \n"
    logo += " |  __ \\         (_)         | |   |  \\/  |                     | |         | |  \n"
    logo += " | |__) | __ ___  _  ___  ___| |_  | \\  / | ___   ___  _ __  ___| |__   ___ | |_ \n"
    logo += " |  ___/ '__/ _ \\| |/ _ \\/ __| __| | |\\/| |/ _ \\ / _ \\| '_ \\/ __| '_ \\ / _ \\| __|\n"
    logo += " | |   | | | (_) | |  __/ (__| |_  | |  | | (_) | (_) | | | \\__ \\ | | | (_) | |_ \n"
    logo += " |_|   |_|  \\___/| |\\___|\\___|\\__| |_|  |_|\\___/ \\___/|_| |_|___/_| |_|\\___/ \\__|\n"
    logo += "                _/ |                                                             \n"
    logo += "               |__/                                                              \n"
    print(logo)


if __name__ == "__main__":
    # Display welcome message
    welcome()

    # Print metadata information
    print(f"Name: {app_name}")
    print(f"Version: {__version__}")
    print(f"Author: {__author__}")
    print(f"License: {__license__}")
    print(f"Description: {__description__}")
    print("\n")

    # Indicate that the application is running
    print("Running application...")

    from domain.services.app_config import AppConfig
    from entrypoints.cli.cli import cli

    # Load configuration
    config = AppConfig()

    # Run the CLI
    cli()
