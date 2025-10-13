import typer
from dotenv import load_dotenv

load_dotenv()

# Import command modules
from .commands import card, archive, auto_image

app = typer.Typer(
    help="MLB Showdown Bot - Create custom MLB Showdown cards",
    pretty_exceptions_enable=False
)

# Add commands
app.add_typer(archive.app, name="archive", help="Archive and manage player statistics")
app.add_typer(auto_image.app, name="auto_image", help="Auto image generation and suggestions")
app.add_typer(card.app, name="card", help="Generate individual player cards")

if __name__ == "__main__":
    app()