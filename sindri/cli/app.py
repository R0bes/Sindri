"""Main CLI app definition."""

import typer

app = typer.Typer(
    name="sindri",
    help=(
        "A project-configurable command palette for common dev workflows.\n\n"
        "Examples:\n"
        "  sindri docker build       # Run docker-build command\n"
        "  sindri d up               # Same, using alias\n"
        "  sindri compose up         # Run compose-up command\n"
        "  sindri c up               # Same, using alias\n"
        "  sindri git commit         # Run git-commit command\n"
        "  sindri g commit           # Same, using alias"
    ),
    add_completion=False,
    no_args_is_help=False,
)
