import typer
from dotenv import load_dotenv

load_dotenv()

# Import command modules
from .commands import card, auto_image, database, set, wotc

app = typer.Typer(
    help="MLB Showdown Bot - Create custom MLB Showdown cards",
    pretty_exceptions_enable=False
)

# Add commands
app.add_typer(database.app, name="database", help="Manages database updates and archiving")
app.add_typer(auto_image.app, name="auto_image", help="Auto image generation and suggestions")
app.add_typer(card.app, name="card", help="Generate individual player cards")
app.add_typer(set.app, name="set", help="Build custom Showdown Bot sets")
app.add_typer(wotc.app, name="wotc", help="Convert WOTC player cards to Showdown Bot format")

if __name__ == "__main__":
    app()