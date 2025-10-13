import typer
from dotenv import load_dotenv

load_dotenv()

# Import command modules
from .commands import card, archive

app = typer.Typer(
    help="MLB Showdown Bot - Create custom MLB Showdown cards",
    pretty_exceptions_enable=False
)

# Add commands
app.add_typer(card.app, name="card", help="Generate individual player cards")
app.add_typer(archive.app, name="archive", help="Archive and manage player statistics")

if __name__ == "__main__":
    app()