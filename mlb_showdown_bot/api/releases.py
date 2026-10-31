import os
import threading
import traceback
from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from ..core.card.images import ImageLibrary
from ..core.database.postgres_db import PostgresDB, StaleEditionError
from ..core.set_builder.foil_selection import FoilSetType, FoilSuggester
from ..core.set_builder.image_match_classifier import ImageMatchCard, ImageMatchClassifier
from ..core.set_builder.release_card_rebuilder import ReleaseCardRebuilder, ReleaseCardRebuildError
from ..core.set_builder.release_images import EditionImagePlan, EditionImageRenderer, ReleaseImageJobCancelled, ReleaseImageStorage
from ..core.set_builder.release_custom_card import ReleaseCustomCard, ReleaseCustomCardError
from ..core.set_builder.release_card_patch import ReleaseCardNumbers, ReleaseCardPatch
from ..core.set_builder.release_draft import ReleaseDraft
from ..core.set_builder.release_review import ReleaseReview
from ..core.set_builder.release_share import ReleaseShareImage
from ..core.set_builder.selection import OtherEditionsRule
from ..core.set_builder.showdown_bot_set import AlgorithmPreviewRequest
from ..core.set_builder.wotc_set_profile import WotcSetProfile
from .image_libraries import UserImageLibraries
from .user_settings import require_auth, optional_user_id
from .utils.view_counter import RecentViews

releases_bp = Blueprint('releases', __name__)

# Renders run as threads on the web dyno. Each holds about one card's images in memory (~130 MB at
# peak, measured), and Pillow releases the GIL, so threads render in parallel. The cap is per dyno,
# since its workers share its memory (see `create_release_image_job`): 3 leaves room for a sim on a
# 1 GB dyno. `RELEASE_IMAGE_MAX_CONCURRENT_PER_DYNO` retunes it without a code change.
_MAX_RENDERS_PER_DYNO = max(1, int(os.environ.get('RELEASE_IMAGE_MAX_CONCURRENT_PER_DYNO', 3)))
_RENDER_BUSY_ERROR = 'Image rendering is busy right now. Try again in a minute.'
_recent_views = RecentViews()


@releases_bp.route('/releases', methods=['GET'])
@require_auth
def get_releases():
    try:
        db = PostgresDB()
        releases = db.get_releases(g.user_id)
        db.close_connection()
        return jsonify(releases), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases', methods=['POST'])
@require_auth
def create_release():
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        if not payload.get('name'):
            return jsonify({'error': 'name is required'}), 400
        db = PostgresDB()
        # Every release starts with a single "main" edition, so the user never has to create one first
        release_id = db.create_release(g.user_id, payload, with_main_edition=True)
        release = db.get_release(release_id, g.user_id)
        db.close_connection()
        return jsonify(release), 201
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/by-slug/<slug>', methods=['GET'])
def get_release_by_slug(slug: str):
    """The release behind a short link (`/r/<slug>`), if the caller can see it."""
    try:
        with PostgresDB() as db:
            release_id = db.get_release_id_by_slug(slug)
            release = db.get_release(release_id, optional_user_id()) if release_id else None
        if release is None:
            return jsonify({'error': 'Release not found'}), 404
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>', methods=['GET'])
def get_release(release_id: str):
    try:
        user_id = optional_user_id()
        db = PostgresDB()
        release = db.get_release(release_id, user_id)
        db.close_connection()
        if release is None:
            return jsonify({'error': 'Release not found'}), 404
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>', methods=['PUT'])
@require_auth
def update_release(release_id: str):
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        for flag in ('is_listed', 'allow_remix'):
            if flag in payload and not isinstance(payload[flag], bool):
                return jsonify({'error': f'{flag} must be true or false'}), 400
        if 'name' in payload:
            if not isinstance(payload['name'], str) or not payload['name'].strip():
                return jsonify({'error': 'Release name cannot be blank'}), 400
            payload['name'] = payload['name'].strip()
        db = PostgresDB()
        updated = db.update_release(release_id, g.user_id, payload)
        if not updated:
            db.close_connection()
            return jsonify({'error': 'Release not found or not owned by user'}), 404
        release = db.get_release(release_id, g.user_id)
        db.close_connection()
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>', methods=['DELETE'])
@require_auth
def delete_release(release_id: str):
    """Delete the release, or retire it if it was ever published or has cards on teams (see
    `PostgresDB.delete_release`). `retired` says which; a retired release keeps its card images."""
    try:
        with PostgresDB() as db:
            result = db.delete_release(release_id, g.user_id)
        if result is None:
            return jsonify({'error': 'Release not found or not owned by user'}), 404
        retired, orphaned_paths = result
        if retired:
            ReleaseImageStorage().delete(orphaned_paths)
        else:
            ReleaseImageStorage().delete_folder(release_id)
        return jsonify({'success': True, 'retired': retired}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


LIVE_EDITION_ERROR = 'This edition has been published. Edit its working copy instead (reload the release).'
STALE_EDITION_ERROR = "This edition changed in another tab or on another device, so your last change wasn't saved. Reload to get the latest."


def _stale_edition_response():
    """409 for a card save based on an older `cards_version` (`code` lets the builder offer a reload)."""
    return jsonify({'error': STALE_EDITION_ERROR, 'code': 'stale_edition'}), 409


def _expected_cards_version(payload: dict) -> int | None:
    """The `cards_version` a card save was based on. Absent (older clients) skips the check."""
    value = payload.get('expected_cards_version')
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _is_live_edition(edition: dict | None) -> bool:
    """A published edition (not a working copy). Its cards may be on teams, so it only changes by publishing."""
    return bool(edition and edition.get('published_at') and not edition.get('draft_of'))


def _owned_release(db: PostgresDB, release_id: str, user_id: str) -> dict | None:
    """The release if the user owns it. `get_release` alone also returns other users' published releases."""
    release = db.get_release(release_id, user_id)
    return release if release is not None and release['created_by'] == user_id else None


@releases_bp.route('/releases/<release_id>/review', methods=['GET'])
@require_auth
def get_release_review(release_id: str):
    """The pre-publish checklist (see `ReleaseReview`) and the release's list tile as others will see it."""
    try:
        with PostgresDB() as db:
            release = _owned_release(db, release_id, g.user_id)
            if release is None:
                return jsonify({'error': 'Release not found or not owned by user'}), 404
            changes = ReleaseDraft(db, release, g.user_id).changes()
            items = ReleaseReview(db, release, g.user_id, UserImageLibraries.for_card_build(g.user_id), changes=changes).run()
            tile = db.get_release_tile(release_id, g.user_id)
        return jsonify({
            'items': [item.model_dump(mode='json') for item in items],
            'tile': tile,
            # None before the first publish, when everything is new
            'changes': changes.model_dump(mode='json') if changes else None,
        }), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/publish', methods=['POST'])
@require_auth
def publish_release(release_id: str):
    """Publish the release: every edition goes public, and an already-published release's working
    copies replace its live editions as a new version (optional `note` in the body). Refused (409,
    with the blocking items) while any review blocker is open."""
    try:
        payload = request.get_json(silent=True) or {}
        note = payload.get('note') if isinstance(payload.get('note'), str) else None
        with PostgresDB() as db:
            release = _owned_release(db, release_id, g.user_id)
            if release is None:
                return jsonify({'error': 'Release not found or not owned by user'}), 404
            changes = ReleaseDraft(db, release, g.user_id).changes()
            # Blockers never depend on photo matches, so skip the Drive lookups
            blockers = [item for item in ReleaseReview(db, release, g.user_id, changes=changes).run() if item.is_blocking]
            if blockers:
                return jsonify({
                    'error': f"Fix {len(blockers)} item{'' if len(blockers) == 1 else 's'} before publishing.",
                    'items': [item.model_dump(mode='json') for item in blockers],
                }), 409
            is_live = any(edition.get('is_published') for edition in release.get('editions') or [])
            if changes is not None and is_live and not changes.has_changes:
                return jsonify({'error': 'There are no changes to publish.'}), 409
            replaced_paths = db.publish_release(
                release_id, g.user_id,
                bump_version=changes is None or changes.has_changes, note=note,
                changes=[edition.summary() for edition in changes.editions if edition.has_changes] if changes else None,
            )
            try:
                # The link preview should show what was just published
                ReleaseShareImage(db).refresh(release_id, request.host)
            except Exception:
                # Link previews retry it on their own; never fail a publish over it
                traceback.print_exc()
            release = db.get_release(release_id, g.user_id)
        ReleaseImageStorage().delete(replaced_paths or [])
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/draft', methods=['POST'])
@require_auth
def start_release_draft(release_id: str):
    """Open private working copies of a published release's editions (no-op for ones that have one)."""
    try:
        with PostgresDB() as db:
            if not db.start_release_draft(release_id, g.user_id):
                return jsonify({'error': 'Release not found or not owned by user'}), 404
            release = db.get_release(release_id, g.user_id)
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/draft', methods=['DELETE'])
@require_auth
def discard_release_draft(release_id: str):
    """Throw away every unpublished change: the working copies and any never-published editions."""
    try:
        with PostgresDB() as db:
            orphaned_paths = db.discard_release_draft(release_id, g.user_id)
            if orphaned_paths is None:
                return jsonify({'error': 'Release not found or not owned by user'}), 404
            release = db.get_release(release_id, g.user_id)
        ReleaseImageStorage().delete(orphaned_paths)
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


def _visible_published_release(db: PostgresDB, release_id: str, user_id: str | None) -> dict | None:
    """The release if this viewer can open it and it's published (likes and views only count there)."""
    release = db.get_release(release_id, user_id)
    if release is None or not any(edition.get('is_published') for edition in release.get('editions') or []):
        return None
    return release


@releases_bp.route('/releases/<release_id>/like', methods=['POST'])
@require_auth
def like_release(release_id: str):
    try:
        with PostgresDB() as db:
            if _visible_published_release(db, release_id, g.user_id) is None:
                return jsonify({'error': 'Release not found'}), 404
            result = db.toggle_release_like(release_id, g.user_id)
        return jsonify(result), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/save', methods=['POST'])
@require_auth
def save_release(release_id: str):
    """Save someone else's published release (or unsave it), so its cards show in the user's card search."""
    try:
        with PostgresDB() as db:
            release = _visible_published_release(db, release_id, g.user_id)
            if release is None:
                return jsonify({'error': 'Release not found'}), 404
            if release['created_by'] == g.user_id:
                return jsonify({'error': 'Your own releases are already in your card search'}), 400
            saved = db.toggle_release_save(release_id, g.user_id)
        return jsonify({'saved': saved}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/remix', methods=['POST'])
@require_auth
def remix_release(release_id: str):
    """Start a new release from someone else's published one (see `PostgresDB.remix_release`). The
    body may set the new release's `name`, `description` and `default_showdown_set`; anything left
    out comes from the source."""
    try:
        payload = request.get_json(silent=True) or {}
        if not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        with PostgresDB() as db:
            source = _visible_published_release(db, release_id, g.user_id)
            if source is None:
                return jsonify({'error': 'Release not found'}), 404
            if source['created_by'] == g.user_id:
                return jsonify({'error': 'This is already your release'}), 400
            if not source.get('allow_remix'):
                return jsonify({'error': "The owner has turned off remixes for this release"}), 403
            name = payload.get('name') if isinstance(payload.get('name'), str) else ''
            description = payload.get('description', source.get('description'))
            description = description.strip() if isinstance(description, str) else ''
            remix_id = db.remix_release(release_id, g.user_id, {
                'name': name.strip() or f"{source['name']} Remix",
                'description': description or None,
                'default_showdown_set': payload.get('default_showdown_set') or source.get('default_showdown_set'),
            })
            if remix_id is None:
                # The owner turned remixes off or unpublished it since the check above
                return jsonify({'error': "This release can't be remixed right now"}), 409
            release = db.get_release(remix_id, g.user_id)
        return jsonify(release), 201
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/saved', methods=['GET'])
@require_auth
def get_saved_releases():
    try:
        with PostgresDB() as db:
            releases = db.get_saved_releases(g.user_id)
        return jsonify(releases), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/view', methods=['POST'])
def record_release_view(release_id: str):
    """Count a visit to a published release. The owner's own visits don't count, nor do repeat
    visits from the same viewer within a few hours (see `RecentViews`)."""
    try:
        user_id = optional_user_id()
        with PostgresDB() as db:
            release = _visible_published_release(db, release_id, user_id)
            if release is None:
                return jsonify({'error': 'Release not found'}), 404
            if user_id is not None and release['created_by'] == user_id:
                return jsonify({'counted': False}), 200
            if not _recent_views.is_new(release_id, user_id):
                return jsonify({'counted': False}), 200
            db.record_release_view(release_id)
        return jsonify({'counted': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/versions', methods=['GET'])
def get_release_versions(release_id: str):
    """The release's published versions, newest first, with each one's note and change summary."""
    try:
        with PostgresDB() as db:
            if db.get_release(release_id, optional_user_id()) is None:
                return jsonify({'error': 'Release not found'}), 404
            versions = db.get_release_versions(release_id)
        return jsonify(versions), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/share_image', methods=['POST'])
def ensure_release_share_image(release_id: str):
    """The published release's link-preview image, rendered now if it's missing or out of date
    (a no-op when it's current). The share sheet calls this, so a release published before share
    images existed, or whose render at publish failed, still gets one."""
    try:
        with PostgresDB() as db:
            path = ReleaseShareImage(db).refresh(release_id, request.host)
        if path is None:
            return jsonify({'error': 'Release not found or not published'}), 404
        return jsonify({'share_image_path': path}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': f"Couldn't make the preview image: {exc}"}), 500


@releases_bp.route('/releases/<release_id>/unpublish', methods=['POST'])
@require_auth
def unpublish_release(release_id: str):
    try:
        with PostgresDB() as db:
            if not db.set_release_published(release_id, g.user_id, False):
                return jsonify({'error': 'Release not found or not owned by user'}), 404
            release = db.get_release(release_id, g.user_id)
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/public', methods=['GET'])
def get_public_releases():
    try:
        limit = min(request.args.get('limit', 50, type=int), 200)
        offset = request.args.get('offset', 0, type=int)
        db = PostgresDB()
        releases = db.get_public_releases(
            limit=limit, offset=offset,
            section=request.args.get('section'), sort=request.args.get('sort', 'updated'),
            search=request.args.get('q'),
        )
        db.close_connection()
        return jsonify(releases), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions', methods=['POST'])
@require_auth
def create_edition(release_id: str):
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        if not payload.get('name'):
            return jsonify({'error': 'name is required'}), 400
        if (duplicate_error := ReleaseCardNumbers.duplicate_error(payload.get('cards'))):
            return jsonify({'error': duplicate_error}), 400
        db = PostgresDB()
        edition_id = db.create_edition(release_id, g.user_id, payload)
        if edition_id is None:
            db.close_connection()
            return jsonify({'error': 'Release not found or not owned by user'}), 404
        edition = db.get_edition(edition_id, g.user_id)
        db.close_connection()
        return jsonify(edition), 201
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>', methods=['GET'])
def get_edition(release_id: str, edition_id: str):
    try:
        user_id = optional_user_id()
        db = PostgresDB()
        edition = db.get_edition(edition_id, user_id)
        db.close_connection()
        if edition is None or edition['release_id'] != release_id:
            return jsonify({'error': 'Edition not found'}), 404
        return jsonify(edition), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>', methods=['PUT'])
@require_auth
def update_edition(release_id: str, edition_id: str):
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400
        if (duplicate_error := ReleaseCardNumbers.duplicate_error(payload.get('cards'))):
            return jsonify({'error': duplicate_error}), 400
        db = PostgresDB()
        if _is_live_edition(db.get_edition(edition_id, g.user_id)):
            db.close_connection()
            return jsonify({'error': LIVE_EDITION_ERROR}), 409
        try:
            updated = db.update_edition(edition_id, g.user_id, payload, expected_cards_version=_expected_cards_version(payload))
        except StaleEditionError:
            db.close_connection()
            return _stale_edition_response()
        if not updated:
            db.close_connection()
            return jsonify({'error': 'Edition not found or not owned by user'}), 404
        if isinstance(payload.get('cards'), list):
            _delete_removed_card_images(db, edition_id)
        edition = db.get_edition(edition_id, g.user_id)
        db.close_connection()
        return jsonify(edition), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


_MAX_CARD_PATCHES = 2000


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/cards', methods=['PATCH'])
@require_auth
def patch_edition_cards(release_id: str, edition_id: str):
    """Save card numbers, tags, cover picks and per-card style overrides without re-sending card
    snapshots (see `ReleaseCardPatch`). Body: `cards`, a list of `{source_card_id, ...changed fields}`."""
    try:
        payload = request.get_json(silent=True) or {}
        raw_patches = payload.get('cards')
        if not isinstance(raw_patches, list) or not raw_patches:
            return jsonify({'error': 'cards must be a non-empty list'}), 400
        if len(raw_patches) > _MAX_CARD_PATCHES:
            return jsonify({'error': f'At most {_MAX_CARD_PATCHES} cards can be changed at once.'}), 400
        try:
            patches = [ReleaseCardPatch(**patch) for patch in raw_patches]
        except (ValidationError, TypeError) as exc:
            return jsonify({'error': str(exc)}), 400

        with PostgresDB() as db:
            state = db.get_owned_edition_card_numbers(release_id, edition_id, g.user_id)
            if state is None:
                return jsonify({'error': 'Edition not found or not owned by user'}), 404
            is_live, card_numbers = state
            if is_live:
                return jsonify({'error': LIVE_EDITION_ERROR}), 409
            if (duplicate_error := ReleaseCardNumbers.patched_duplicate_error(card_numbers, patches)):
                return jsonify({'error': duplicate_error}), 400
            try:
                cards_version = db.patch_release_cards(
                    edition_id, [(patch.source_card_id, patch.changes()) for patch in patches],
                    expected_cards_version=_expected_cards_version(payload),
                )
            except StaleEditionError:
                return _stale_edition_response()
        return jsonify({'success': True, 'cards_version': cards_version}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>', methods=['DELETE'])
@require_auth
def delete_edition(release_id: str, edition_id: str):
    """Delete an edition (see `PostgresDB.remove_edition`): a published one is staged until the next
    publish, a never-published one goes now. Returns the `outcome` and the updated release."""
    try:
        with PostgresDB() as db:
            result = db.remove_edition(edition_id, g.user_id) if _owned_edition(db, release_id, edition_id, g.user_id) else None
            if result is None:
                return jsonify({'error': 'Edition not found or not owned by user'}), 404
            outcome = result[1]
            release = db.get_release(release_id, g.user_id)
        if outcome == 'deleted':
            ReleaseImageStorage().delete_folder(release_id, edition_id)
        return jsonify({'outcome': outcome, 'release': release}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/restore', methods=['POST'])
@require_auth
def restore_edition(release_id: str, edition_id: str):
    """Undo a published edition's staged removal. Returns the updated release."""
    try:
        with PostgresDB() as db:
            if _owned_edition(db, release_id, edition_id, g.user_id) is None or not db.restore_edition(edition_id, g.user_id):
                return jsonify({'error': 'Edition not found or not owned by user'}), 404
            release = db.get_release(release_id, g.user_id)
        return jsonify(release), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/algorithm/wotc_profiles', methods=['GET'])
def get_wotc_set_profiles():
    """Position counts and average points of each WOTC base set, used as Algorithm blueprints"""
    try:
        profiles = WotcSetProfile.load_all()
        return jsonify([profile.model_dump() for profile in profiles.values()]), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/algorithm/preview', methods=['POST'])
@require_auth
def preview_algorithm(release_id: str, edition_id: str):
    """Run ShowdownBotSet against the request config and return a preview player pool.
    Does not persist anything to the edition — the frontend commits the result via the
    existing PUT /editions/<edition_id> `cards` mechanism.

    Admins can pass `rerun_cards: true` to rebuild each selected card through the current
    `ShowdownPlayerCard` algorithm instead of returning the archived version."""
    try:
        payload = request.get_json(silent=True)
        if not payload or not isinstance(payload, dict):
            return jsonify({'error': 'Request body must be a JSON object'}), 400

        rerun_cards = bool(payload.pop('rerun_cards', False))
        if rerun_cards and not getattr(g, 'is_admin', False):
            return jsonify({'error': 'Admin access required to re-run cards'}), 403

        db = PostgresDB()
        # Owner only: it's the heaviest endpoint, and `get_edition` alone also returns others' published editions
        if _owned_edition(db, release_id, edition_id, g.user_id) is None:
            db.close_connection()
            return jsonify({'error': 'Edition not found or not owned by user'}), 404

        try:
            algorithm_request = AlgorithmPreviewRequest(**payload)
            other_edition_players = (
                db.get_other_edition_players(release_id, edition_id, g.user_id)
                if algorithm_request.other_editions_rule != OtherEditionsRule.ALLOW else None
            )
            showdown_set = algorithm_request.to_showdown_bot_set(other_edition_players)
        except ValidationError as exc:
            db.close_connection()
            return jsonify({'error': str(exc)}), 400

        players = showdown_set.build_preview_rows(db, rerun_cards=rerun_cards, variable_speed=algorithm_request.variable_speed)
        db.close_connection()

        return jsonify({
            'players': players,
            'summary': {
                'requested_set_size': showdown_set.set_size,
                'actual_count': len(players),
                'warnings': showdown_set.warnings,
                'cut_lines': showdown_set.cut_lines,
            },
        }), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/foils/suggest', methods=['POST'])
@require_auth
def suggest_edition_foils(release_id: str, edition_id: str):
    """Cards to tag `FOIL` so about 15% of the edition is foil (see `FoilSuggester`). Body: `set_type`
    (`BASE` or `EXPANSION`). Does not persist: the builder applies picks through the card PATCH."""
    try:
        payload = request.get_json(silent=True) or {}
        try:
            set_type = FoilSetType(payload.get('set_type', FoilSetType.BASE.value))
        except ValueError:
            return jsonify({'error': 'set_type must be BASE or EXPANSION'}), 400

        with PostgresDB() as db:
            edition = _owned_edition(db, release_id, edition_id, g.user_id)
            if edition is None:
                return jsonify({'error': 'Edition not found or not owned by user'}), 404
            result = FoilSuggester.for_edition(db, edition.get('cards') or [], set_type).suggest()
        return jsonify(result.model_dump()), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/cards/rebuild', methods=['POST'])
@require_auth
def rebuild_edition_card(release_id: str, edition_id: str):
    """The snapshot of one of the edition's cards at another `chart_version`. Does not persist —
    the frontend saves the returned snapshot via the PUT /editions/<edition_id> `cards` mechanism."""
    try:
        payload = request.get_json(silent=True) or {}
        source_card_id = payload.get('source_card_id')
        try:
            chart_version = int(payload.get('chart_version'))
        except (TypeError, ValueError):
            return jsonify({'error': 'chart_version must be a number'}), 400

        with PostgresDB() as db:
            edition = _owned_edition(db, release_id, edition_id, g.user_id)
            if edition is None:
                return jsonify({'error': 'Edition not found or not owned by user'}), 404
            card = next((c for c in edition.get('cards') or [] if c.get('source_card_id') == source_card_id), None)
            if card is None:
                return jsonify({'error': 'Card not found in this edition'}), 404
            try:
                snapshot = ReleaseCardRebuilder(db).snapshot_at_chart_version(
                    card.get('card_snapshot') or {}, card.get('source_card_type'), chart_version,
                )
            except ReleaseCardRebuildError as exc:
                return jsonify({'error': str(exc)}), 400

        return jsonify({'card_snapshot': snapshot}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/cards/custom', methods=['POST'])
@require_auth
def custom_edition_card(release_id: str, edition_id: str):
    """The release card snapshot of one of the user's Custom Card Builder cards. Does not persist —
    the frontend saves the returned snapshot via the PUT /editions/<edition_id> `cards` mechanism."""
    try:
        payload = request.get_json(silent=True) or {}
        custom_card_id = str(payload.get('custom_card_id') or '').strip()
        if not custom_card_id:
            return jsonify({'error': 'custom_card_id is required'}), 400

        with PostgresDB() as db:
            if _owned_edition(db, release_id, edition_id, g.user_id) is None:
                return jsonify({'error': 'Edition not found or not owned by user'}), 404
            try:
                snapshot = ReleaseCustomCard(db).snapshot(custom_card_id)
            except ReleaseCustomCardError as exc:
                return jsonify({'error': str(exc)}), 404

        return jsonify({'card_snapshot': snapshot}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


# =============================================================================
# EDITION IMAGES
# =============================================================================

def _delete_removed_card_images(db: PostgresDB, edition_id: str) -> None:
    """After a cards save, drop image rows + files for cards no longer in the edition. Best effort:
    a failure never fails the save, and leftovers are swept by the next render or the janitor."""
    try:
        ReleaseImageStorage().delete(db.delete_release_card_images_not_in_edition(edition_id))
    except Exception:
        traceback.print_exc()


def _owned_edition(db: PostgresDB, release_id: str, edition_id: str, user_id: str) -> dict | None:
    """The edition with its cards if it belongs to `release_id` and the user owns that release.
    `get_edition` alone also returns other users' published editions."""
    release = db.get_release(release_id, user_id)
    if release is None or release['created_by'] != user_id:
        return None
    edition = db.get_edition(edition_id, user_id)
    if edition is None or edition['release_id'] != release_id:
        return None
    return edition


def _run_render_job(job_id: str, edition: dict, image_libraries: list[ImageLibrary], source_card_ids: list[str] | None) -> None:
    """Worker thread body. Its job row holds the dyno's render slot until it finishes."""
    with PostgresDB() as db:
        try:
            EditionImageRenderer(
                db=db, job_id=job_id, edition=edition,
                image_libraries=image_libraries, source_card_ids=source_card_ids,
            ).run()
            db.finish_release_image_job(job_id)
        except ReleaseImageJobCancelled:
            print(f"[release images {job_id}] cancelled")
        except Exception as exc:
            traceback.print_exc()
            db.finish_release_image_job(job_id, error=str(exc)[:500])


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/images', methods=['GET'])
def get_edition_images(release_id: str, edition_id: str):
    """Each card's image status (rendered / stale / failed / missing) and the latest render job.
    Visible to anyone who can view the edition."""
    try:
        with PostgresDB() as db:
            edition = db.get_edition(edition_id, optional_user_id())
            if edition is None or edition['release_id'] != release_id:
                return jsonify({'error': 'Edition not found'}), 404
            images = EditionImagePlan(edition).card_statuses(db.get_release_card_images(edition_id))
            job = db.get_latest_release_image_job(edition_id)
        return jsonify({'images': images, 'job': job}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/images/render', methods=['POST'])
@require_auth
def render_edition_images(release_id: str, edition_id: str):
    """Queue a background job rendering the edition's missing/out-of-date images. Optional
    `source_card_ids` limits it to those cards."""
    try:
        payload = request.get_json(silent=True) or {}
        source_card_ids = payload.get('source_card_ids')
        if source_card_ids is not None and (not isinstance(source_card_ids, list) or not all(isinstance(i, str) for i in source_card_ids)):
            return jsonify({'error': 'source_card_ids must be a list of strings'}), 400

        with PostgresDB() as db:
            edition = _owned_edition(db, release_id, edition_id, g.user_id)
            if edition is None:
                return jsonify({'error': 'Edition not found or not owned by user'}), 404
            if _is_live_edition(edition):
                return jsonify({'error': LIVE_EDITION_ERROR}), 409
            job_id, busy = db.create_release_image_job(
                edition_id, g.user_id, dyno=os.environ.get('DYNO'), max_active_on_dyno=_MAX_RENDERS_PER_DYNO,
            )
            if busy == 'edition_busy':
                return jsonify({'error': 'Images are already rendering for this edition.'}), 409
            if busy == 'dyno_busy':
                return jsonify({'error': _RENDER_BUSY_ERROR}), 429
            job = db.get_latest_release_image_job(edition_id)

        try:
            threading.Thread(
                target=_run_render_job,
                args=(job_id, edition, UserImageLibraries.for_card_build(g.user_id), source_card_ids),
                name=f'release-images-{job_id[:8]}', daemon=True,
            ).start()
        except Exception as exc:
            # Finishing the job frees its slot; the worker would have, had it started
            with PostgresDB() as db:
                db.finish_release_image_job(job_id, error=str(exc)[:500])
            raise

        return jsonify({'job': job}), 202
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/images/cancel', methods=['POST'])
@require_auth
def cancel_edition_images(release_id: str, edition_id: str):
    try:
        with PostgresDB() as db:
            if _owned_edition(db, release_id, edition_id, g.user_id) is None:
                return jsonify({'error': 'Edition not found or not owned by user'}), 404
            cancelled = db.cancel_release_image_job(edition_id)
            job = db.get_latest_release_image_job(edition_id)
        if not cancelled:
            return jsonify({'error': 'No render in progress.'}), 409
        return jsonify({'job': job}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


_MAX_IMAGE_MATCH_CARDS = 2000


@releases_bp.route('/releases/<release_id>/editions/<edition_id>/images/matches', methods=['POST'])
@require_auth
def classify_edition_image_matches(release_id: str, edition_id: str):
    """Live auto image match per card snapshot, searching the owner's image libraries (their Google
    Drive folders + Showdown Bot) in the order a render would. Takes `cards` (snapshots) in the body so
    unsaved algorithm previews can be checked too; `refresh: true` re-reads the libraries from Drive."""
    try:
        payload = request.get_json(silent=True) or {}
        snapshots = payload.get('cards')
        if not isinstance(snapshots, list) or not all(isinstance(s, dict) for s in snapshots):
            return jsonify({'error': 'cards must be a list of card snapshots'}), 400
        if len(snapshots) > _MAX_IMAGE_MATCH_CARDS:
            return jsonify({'error': f'At most {_MAX_IMAGE_MATCH_CARDS} cards can be checked at once.'}), 400

        with PostgresDB() as db:
            if _owned_edition(db, release_id, edition_id, g.user_id) is None:
                return jsonify({'error': 'Edition not found or not owned by user'}), 404

        cards = [card for card in map(ImageMatchCard.from_snapshot, snapshots) if card]
        classifier = ImageMatchClassifier(UserImageLibraries.for_card_build(g.user_id), refresh=bool(payload.get('refresh')))
        return jsonify(classifier.classify(cards)), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500
