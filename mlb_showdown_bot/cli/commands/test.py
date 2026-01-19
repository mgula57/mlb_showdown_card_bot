import typer

from ...scripts.test_card_generation import run_tests

app = typer.Typer()

@app.command("test")
def testing(
    skip_images: bool = typer.Option(False, "--skip_images", "-no_img", help="Skip running images."),
):
    """Run card generation tests for various players and sets"""
    run_tests(skip_images=skip_images)

# Make set builder the default command
@app.callback(invoke_without_command=True)
def test_main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        ctx.invoke(testing)