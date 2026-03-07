import typer
import time

# Import business logic
from ...core.card.wotc.wotc_player_cards import WotcPlayerCardSet, Set, PostgresDB

app = typer.Typer()

@app.command("convert")
def wotc_conversion(
    env: str = typer.Option("dev", "--env", "-e", help="Environment to run in (dev, prod)"),
    sets: str = typer.Option(None, "--sets", "-s", help="Which sets to convert, comma-separated."),
    upload_to_postgres: bool = typer.Option(False, "--upload_to_postgres", "-pg", help="Upload converted data to Postgres"),
    drop_existing: bool = typer.Option(False, "--drop_existing", "-d", help="Drop existing table before uploading new data")
):
    """Archive player stats to Postgres"""
    sets_list = sets.split(',') if sets else ['2000', '2001', '2002', '2003', '2004', '2005',]
    wotc_set = WotcPlayerCardSet(sets=[Set(s) for s in sets_list])

    if upload_to_postgres:
        start_time = time.time()
        is_prod = env.lower() == 'prod'
        db = PostgresDB(is_archive=is_prod)
        db.upload_wotc_card_data(wotc_card_data=list(wotc_set.cards.values()), drop_existing=drop_existing)
        end_time = time.time()
        print(f"✅ Uploaded WOTC data to Postgres in {end_time - start_time:.2f} seconds.")
    else:
        wotc_set.export_to_local_file()
    

# Make set builder the default command
@app.callback(invoke_without_command=True)
def wotc_convert_main(ctx: typer.Context):
    """Convert WOTC player cards to Showdown Bot format"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(wotc_conversion)