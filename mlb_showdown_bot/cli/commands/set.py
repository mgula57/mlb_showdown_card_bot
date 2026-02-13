import typer
import time

# Import business logic
from ...core.set_builder.showdown_bot_set import ShowdownBotSet

app = typer.Typer()

@app.command("build")
def set_builder(
    years: str = typer.Option(None, "--years", "-y", help="Which year(s) to archive."),
    showdown_sets: str = typer.Option("CLASSIC,EXPANDED,2000,2001,2002,2003,2004,2005", "--showdown_sets", "-s", help="Showdown Set(s) to use, comma-separated."),
    set_size: int = typer.Option(100, "--set_size", "-ss", help="Number of cards to include in the set."),
    team_breakdown: str = typer.Option(None, "--team_breakdown", "-tb", help="Show team breakdown for a specific team."),
    ideal_low_point_percentage: float = typer.Option(None, "--ideal_low_point_percentage", "-ilpp", help="Ideal percentage of low-point cards in the set."),
    manually_included_ids: str = typer.Option(None, "--manually_included_ids", "-inc", help="Specific player IDs to include in the set, comma-separated."),
    manually_excluded_ids: str = typer.Option(None, "--manually_excluded_ids", "-exc", help="Specific player IDs to exclude from the set, comma-separated."),
    build_images: bool = typer.Option(False, "--build_images", "-img", help="Optionally build card images for the set after building."),
):
    """Archive player stats to Postgres"""

    start_time = time.time()
    
    try:
        # Parse showdown sets
        showdown_set_list = [s.strip() for s in showdown_sets.split(',') if s.strip()]

        # Parse years
        year_list = [int(y.strip()) for y in years.split(',')] if years else []

        # BUILD THE SET
        showdown_bot_set = ShowdownBotSet(
            years=year_list,
            showdown_sets=showdown_set_list,
            set_size=set_size,
            ideal_low_point_percentage=ideal_low_point_percentage,
            manually_included_ids=[pid.strip() for pid in manually_included_ids.split(',')] if manually_included_ids else None,
            manually_excluded_ids=[pid.strip() for pid in manually_excluded_ids.split(',')] if manually_excluded_ids else None
        )
        showdown_bot_set.build_set_player_list(show_team_breakdown=team_breakdown)
        if build_images:
            showdown_bot_set.generate_showdown_cards_for_final_players()

    except Exception as e:
        # Full traceback
        import traceback
        traceback.print_exc()

    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # Format the elapsed time nicely
        if elapsed_time < 60:
            time_str = f"{elapsed_time:.2f} seconds"
        elif elapsed_time < 3600:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            time_str = f"{minutes}m {seconds:.1f}s"
        else:
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = elapsed_time % 60
            time_str = f"{hours}h {minutes}m {seconds:.1f}s"
        
        print(f"\n✅ Set Builder operation completed in {time_str}")


# Make set builder the default command
@app.callback(invoke_without_command=True)
def set_builder_main(ctx: typer.Context):
    """Build a Showdown Bot Set"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(set_builder)