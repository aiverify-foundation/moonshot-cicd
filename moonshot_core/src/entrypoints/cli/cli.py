import asyncio
import logging
from typing import Any, Generator

import click
import toml
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Column

from adapters.api.api_adapter import ApiAdapter
from domain.services.app_config import AppConfig

# Configure rich logging
logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)
logger = logging.getLogger("rich")

with open("pyproject.toml", "r") as f:
    pyproject = toml.load(f)

app_name = pyproject["tool"]["poetry"]["name"]
__version__ = pyproject["tool"]["poetry"]["version"]
__author__ = pyproject["tool"]["poetry"]["authors"][0]
__license__ = pyproject["tool"]["poetry"]["license"]
__description__ = pyproject["tool"]["poetry"]["description"]


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


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    Command-line interface group
    """
    # If no subcommand is invoked, show welcome page
    if ctx.invoked_subcommand is None:
        welcome()
        print(f"Name: {app_name}")
        print(f"Version: {__version__}")
        print(f"Author: {__author__}")
        print(f"License: {__license__}")
        print(f"Description: {__description__}")
        print("\n")
        print("Running application...")
    AppConfig()
    pass


@click.command()
@click.argument("run_id")
@click.argument("test_config_id")
@click.argument("connector")
def create_run_test(run_id: str, test_config_id: str, connector: str) -> None:
    progress_manager.title = f"Moonshot Run Test: {test_config_id}"
    progress_manager.test_info = f"Run ID: {run_id}\nTest Configuration ID: {test_config_id}\nConnector: {connector}"

    async def run_create_run_test():
        run_api_adapter = ApiAdapter()
        await run_api_adapter.create_run_test(run_id, test_config_id, connector)

    # run scan asynchronously
    asyncio.run(run_create_run_test())


cli.add_command(create_run_test, "run")


# Progress Bar and Callback Fn
class MoonshotProgressBar(Progress):
    """
    Override Progress class to define own Progressbar styling
    """

    def __init__(self, *columns, title, **kwargs):
        self.title = title
        super().__init__(*columns, **kwargs)

    def get_renderables(self) -> Generator[Panel, Any, Any]:
        """
        Generate and yield a Panel containing the tasks table.

        This method creates a Panel with the tasks table and applies
        styling such as title and border color.

        Returns:
            Panel: A styled Panel containing the tasks table.
        """
        yield Panel(
            self.make_tasks_table(self.tasks),
            title=self.title,
            title_align="left",
            border_style="white",
        )


class ProgressManager:
    def __init__(self):
        self.title = ""
        self.test_info = ""
        self.progress = None
        self.is_started = False
        self.task_id = None

    def start_progress(self, total: int) -> None:
        """
        Initialize and start the progress bar for tracking task completion.

        This method sets up a progress bar with various columns to display
        task progress, elapsed time, and additional test information. It
        also initializes the task within the progress bar and marks the
        progress as started.

        Args:
            total (int): The total number of tasks to be processed.
        """
        bar_column = BarColumn(bar_width=None, table_column=Column(ratio=2))
        text_column_2 = TextColumn(
            self.test_info, table_column=Column(ratio=1), justify="right"
        )
        self.progress = MoonshotProgressBar(
            SpinnerColumn(),
            bar_column,
            TaskProgressColumn(),
            TimeElapsedColumn(),
            text_column_2,
            transient=False,
            title=self.title,
        )
        self.progress.refresh()
        self.progress.start()
        self.is_started = True
        self.test_info = "This is my test Info"
        self.task_id = self.progress.add_task("Processing prompts", total=total)

    def update_progress(self, completed: int) -> None:
        """
        Update the progress of the current task.

        Args:
            completed (int): The number of completed tasks to update in the progress bar.
        """
        if self.task_id is not None and self.progress is not None:
            self.current_task = self.progress.update(self.task_id, completed=completed)

    def complete_progress(self) -> None:
        """
        Complete the current progress task and reset the progress manager state.

        This method updates the progress to mark the task as completed, stops the progress bar,
        and resets the internal state of the progress manager, including the task ID and the
        started status.
        """
        if self.task_id is not None and self.progress is not None:
            self.progress.update(
                self.task_id, completed=self.progress.tasks[self.task_id].total
            )
            self.progress.stop()
            self.is_started = False
            self.task_id = None


def update_tasks_status(
    state: str | None = None,
    total_prompts: int | None = None,
    completed_count: int | None = None,
    stage: int | None = None,
    message: str | None = None,
) -> None:
    """
    Update the status of tasks and print the results.

    Args:
        state (str | None, optional): The current status of the task. Defaults to None.
        total_prompts (int | None, optional): The total number of prompts to process. Defaults to None.
        completed_count (int | None, optional): The number of prompts that have been completed. Defaults to None.
        index (int | None, optional): The current index of the prompt being processed. Defaults to None.
        stage (int | None, optional): The current stage number of the task. Defaults to None.
        message (str | None, optional): The message to display for the current task. Defaults to None.
    """
    COMPLETE_PROMPT_CALLBACK = (
        "[TaskManager] {completed_count} out of {total_prompts} prompts completed. "
        "Status: {state}"
    )

    if stage is not None and message is not None:
        logger.info(f"[Stage {stage}] {message}")
        pass
    else:
        if state == "completed":
            logger.info(
                COMPLETE_PROMPT_CALLBACK.format(
                    completed_count=completed_count,
                    total_prompts=total_prompts,
                    state=state,
                )
            )
            if completed_count is not None and total_prompts is not None:
                if completed_count < total_prompts:
                    progress_manager.update_progress(completed=completed_count)
                else:
                    progress_manager.complete_progress()

        elif state == "running":
            if total_prompts and progress_manager.task_id is None:
                progress_manager.start_progress(total=total_prompts)
                if completed_count is not None:
                    progress_manager.update_progress(completed=completed_count)


progress_manager = ProgressManager()

if __name__ == "__main__":
    cli()
