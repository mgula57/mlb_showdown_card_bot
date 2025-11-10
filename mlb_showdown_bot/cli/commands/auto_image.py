import typer
from typing import Optional

from ...scripts.auto_image_suggestions import generate_auto_image_suggestions

app = typer.Typer()

@app.command("suggestions")
def auto_image_suggestions(
    ctx: typer.Context,
    player_subtype: Optional[str] = typer.Option(None, "--player_subtype", "-pst", help="Player Sub Types (POSITION_PLAYER, STARTING_PITCHER, RELIEF_PITCHER)"),
    hof: bool = typer.Option(False, "--hof", help="Only Hall of Fame Players"),
    mvp: bool = typer.Option(False, "--mvp", "-v", help="Only MVPs"),
    cya: bool = typer.Option(False, "--cya", "-cy", help="Only CYAs"),
    gold_glove: bool = typer.Option(False, "--gold_glove", "-gg", help="Only Gold Glove Winners"),
    year_start: Optional[int] = typer.Option(None, "--year_start", "-ys", help="Optional year start filter"),
    year_end: Optional[int] = typer.Option(None, "--year_end", "-ye", help="Optional year end filter"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Optional limit"),
    team: Optional[str] = typer.Option(None, "--team", "-tm", help="Optional team filter"),
    year_threshold: Optional[int] = typer.Option(None, "--year_threshold", "-yt", help="Optional year threshold. Only includes images that are <= the threshold."),
    sort_field: str = typer.Option("bWAR", "--sort", help="Optional sort field"),
):
    """Suggest auto image generation for players"""
    
    # Get all CLI parameters
    params = ctx.params

    # Run the suggestions script
    generate_auto_image_suggestions(**params)


# Make archive the default command
@app.callback(invoke_without_command=True)
def auto_image_main(ctx: typer.Context):
    """Auto image operations"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(auto_image_suggestions)