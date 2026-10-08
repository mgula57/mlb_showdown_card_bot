import typer

from ...scripts.test_card_generation import run_tests
from ...core.shared.google_drive import UserDriveClient, UserDriveFolder, UserDriveFolderError

app = typer.Typer()

@app.command("test")
def testing(
    skip_images: bool = typer.Option(False, "--skip_images", "-no_img", help="Skip running images."),
):
    """Run card generation tests for various players and sets"""
    run_tests(skip_images=skip_images)

@app.command("user_drive")
def user_drive(
    folder: str = typer.Argument(..., help="Google Drive folder URL or id, shared (Viewer) with the user-drive service account."),
):
    """Verify the user-drive service account can read a shared folder and list its files"""
    print(f"Service account: {UserDriveClient.service_account_email() or f'<missing {UserDriveClient.CREDENTIALS_ENV_VAR}>'}")
    try:
        summary = UserDriveFolder(folder).verify()
    except UserDriveFolderError as err:
        print(f"FAILED: {err}")
        raise typer.Exit(code=1)

    print(f"Folder: {summary.name} ({summary.folder_id})  canEdit={summary.can_edit}")
    print(f"Images ({len(summary.image_files)}):")
    for file in summary.image_files:
        print(f"  {file['name']}  [{file['id']}]")
    if summary.other_files:
        print(f"Skipped non-image files ({len(summary.other_files)}):")
        for file in summary.other_files:
            print(f"  {file['name']}  ({file.get('mimeType')})")
    print("PASSED")

# Make set builder the default command
@app.callback(invoke_without_command=True)
def test_main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        ctx.invoke(testing)