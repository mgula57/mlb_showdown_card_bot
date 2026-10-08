import uuid
import traceback
from flask import Blueprint, g, jsonify, request

from .user_settings import require_auth
from ..core.card.images import ImageLibrary
from ..core.database.postgres_db import PostgresDB
from ..core.shared.google_drive import UserDriveClient, UserDriveFolder, UserDriveFolderError, UserDriveFolderSummary

image_libraries_bp = Blueprint('image_libraries', __name__)


class UserImageLibraries:
    """A user's connected Google Drive image libraries and the order they're searched for auto images."""

    MAX_LIBRARIES = 5
    UNRECOGNIZED_EXAMPLES_LIMIT = 5

    @classmethod
    def for_card_build(cls, user_id: str | None) -> list[ImageLibrary]:
        """Libraries to search for a card build, in the user's order. Anonymous users get the Showdown Bot library."""
        if not user_id:
            return [ImageLibrary.showdown_bot()]
        try:
            with PostgresDB() as db:
                rows = db.get_user_image_libraries(user_id)
                order = (db.get_user_settings(user_id) or {}).get('image_library_order')
        except Exception:
            # NEVER FAIL A CARD BUILD OVER LIBRARY LOOKUP
            traceback.print_exc()
            return [ImageLibrary.showdown_bot()]
        return ImageLibrary.ordered([cls._library(row) for row in rows], order)

    @staticmethod
    def _library(row: dict) -> ImageLibrary:
        return ImageLibrary(id=row['id'], name=row['name'], folder_id=row['folder_id'])

    @classmethod
    def summary_json(cls, summary: UserDriveFolderSummary) -> dict:
        """Connection test result shown in the setup flow."""
        unrecognized = [f['name'] for f in summary.image_files if not ImageLibrary.is_recognized_file_name(f['name'])]
        return {
            'folder_id': summary.folder_id,
            'name': summary.name,
            'image_count': len(summary.image_files),
            'recognized_image_count': len(summary.image_files) - len(unrecognized),
            'unrecognized_examples': unrecognized[:cls.UNRECOGNIZED_EXAMPLES_LIMIT],
            'other_file_count': len(summary.other_files),
        }

    @classmethod
    def overview_json(cls, user_id: str) -> dict:
        """Everything the Account page needs: libraries, search order, and the email to share folders with."""
        with PostgresDB() as db:
            rows = db.get_user_image_libraries(user_id)
            order = (db.get_user_settings(user_id) or {}).get('image_library_order')
        ordered = ImageLibrary.ordered([cls._library(row) for row in rows], order)
        return {
            'service_account_email': UserDriveClient.service_account_email(),
            'libraries': [{k: v for k, v in row.items() if k != 'owner_user_id'} for row in rows],
            'order': [lib.id for lib in ordered],
        }


def _verify_folder(payload: dict | None) -> UserDriveFolderSummary:
    """Verify the folder in the request body. Raises UserDriveFolderError with a user-facing message."""
    if UserDriveClient.service_account_email() is None:
        raise UserDriveFolderError('Google Drive libraries are temporarily unavailable. Please try again later.')
    folder = (payload or {}).get('folder')
    if not isinstance(folder, str) or not folder.strip():
        raise UserDriveFolderError('Paste your Google Drive folder link.')
    return UserDriveFolder(folder).verify()


@image_libraries_bp.route('/user/image_libraries', methods=['GET'])
@require_auth
def get_image_libraries():
    try:
        return jsonify(UserImageLibraries.overview_json(g.user_id)), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@image_libraries_bp.route('/user/image_libraries/test', methods=['POST'])
@require_auth
def test_image_library():
    """Check the bot can read the folder, without saving it."""
    try:
        summary = _verify_folder(request.get_json(silent=True))
        return jsonify(UserImageLibraries.summary_json(summary)), 200
    except UserDriveFolderError as err:
        return jsonify({'error': str(err)}), 400
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': 'Could not reach Google Drive. Please try again.'}), 500


@image_libraries_bp.route('/user/image_libraries', methods=['POST'])
@require_auth
def save_image_library():
    """Verify and save a folder. Re-saving an already connected folder refreshes its name and counts."""
    try:
        summary_json = UserImageLibraries.summary_json(_verify_folder(request.get_json(silent=True)))
        with PostgresDB() as db:
            existing = db.get_user_image_libraries(g.user_id)
            is_new = all(row['folder_id'] != summary_json['folder_id'] for row in existing)
            if is_new and len(existing) >= UserImageLibraries.MAX_LIBRARIES:
                return jsonify({'error': f'You can connect up to {UserImageLibraries.MAX_LIBRARIES} folders.'}), 400
            db.upsert_user_image_library(
                user_id=g.user_id,
                id=str(uuid.uuid4()),
                folder_id=summary_json['folder_id'],
                name=summary_json['name'],
                image_count=summary_json['image_count'],
                recognized_image_count=summary_json['recognized_image_count'],
            )
        return jsonify({**UserImageLibraries.overview_json(g.user_id), 'test': summary_json}), 200
    except UserDriveFolderError as err:
        return jsonify({'error': str(err)}), 400
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': 'Could not save the folder. Please try again.'}), 500


@image_libraries_bp.route('/user/image_libraries/<library_id>', methods=['DELETE'])
@require_auth
def delete_image_library(library_id: str):
    try:
        with PostgresDB() as db:
            deleted = db.delete_user_image_library(g.user_id, library_id)
        if not deleted:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(UserImageLibraries.overview_json(g.user_id)), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@image_libraries_bp.route('/user/image_libraries/order', methods=['PUT'])
@require_auth
def update_image_library_order():
    payload = request.get_json(silent=True) or {}
    order = payload.get('order')
    if not isinstance(order, list) or not all(isinstance(lib_id, str) for lib_id in order):
        return jsonify({'error': 'order must be a list of library ids'}), 400
    try:
        with PostgresDB() as db:
            valid_ids = {row['id'] for row in db.get_user_image_libraries(g.user_id)} | {ImageLibrary.SHOWDOWN_BOT_ID}
            if not set(order) <= valid_ids or len(set(order)) != len(order):
                return jsonify({'error': 'order contains unknown or duplicate library ids'}), 400
            db.upsert_user_settings(g.user_id, {'image_library_order': order})
        return jsonify(UserImageLibraries.overview_json(g.user_id)), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
