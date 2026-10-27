import os
import threading
import traceback
from flask import Blueprint, g, jsonify, request
from pydantic import ValidationError
from ..core.card.images import ImageLibrary
from ..core.database.postgres_db import PostgresDB
from ..core.set_builder.image_match_classifier import ImageMatchCard, ImageMatchClassifier
from ..core.set_builder.release_card_rebuilder import ReleaseCardRebuilder, ReleaseCardRebuildError
from ..core.set_builder.release_images import EditionImagePlan, EditionImageRenderer, ReleaseImageJobCancelled, ReleaseImageStorage
from ..core.set_builder.release_draft import ReleaseDraft
from ..core.set_builder.release_review import ReleaseReview
from ..core.set_builder.selection import OtherEditionsRule
from ..core.set_builder.showdown_bot_set import AlgorithmPreviewRequest
from ..core.set_builder.wotc_set_profile import WotcSetProfile
from .image_libraries import UserImageLibraries
from .user_settings import require_auth, optional_user_id

releases_bp = Blueprint('releases', __name__)

# Rendering is CPU- and memory-heavy Pillow work on the web dyno. Per worker process, like the
# sim cap; `RELEASE_IMAGE_MAX_CONCURRENT` retunes it without a code change.
_MAX_CONCURRENT_RENDERS = max(1, int(os.environ.get('RELEASE_IMAGE_MAX_CONCURRENT', 1)))
_render_slots = threading.BoundedSemaphore(_MAX_CONCURRENT_RENDERS)


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
        release_id = db.create_release(g.user_id, payload)
        release = db.get_release(release_id, g.user_id)
        db.close_connection()
        return jsonify(release), 201
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
    try:
        db = PostgresDB()
        deleted = db.delete_release(release_id, g.user_id)
        db.close_connection()
        if not deleted:
            return jsonify({'error': 'Release not found or not owned by user'}), 404
        ReleaseImageStorage().delete_folder(release_id)
        return jsonify({'success': True}), 200
    except Exception as exc:
        traceback.print_exc()
        return jsonify({'error': str(exc)}), 500


LIVE_EDITION_ERROR = 'This edition has been published. Edit its working copy instead (reload the release).'


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
        releases = db.get_public_releases(limit=limit, offset=offset)
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
        db = PostgresDB()
        if _is_live_edition(db.get_edition(edition_id, g.user_id)):
            db.close_connection()
            return jsonify({'error': LIVE_EDITION_ERROR}), 409
        updated = db.update_edition(edition_id, g.user_id, payload)
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


@releases_bp.route('/releases/<release_id>/editions/<edition_id>', methods=['DELETE'])
@require_auth
def delete_edition(release_id: str, edition_id: str):
    try:
        db = PostgresDB()
        deleted_release_id = db.delete_edition(edition_id, g.user_id)
        db.close_connection()
        if not deleted_release_id:
            return jsonify({'error': 'Edition not found or not owned by user'}), 404
        ReleaseImageStorage().delete_folder(deleted_release_id, edition_id)
        return jsonify({'success': True}), 200
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
        edition = db.get_edition(edition_id, g.user_id)
        if edition is None or edition['release_id'] != release_id:
            db.close_connection()
            return jsonify({'error': 'Edition not found'}), 404

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
            },
        }), 200
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
    """Worker thread body. Owns a render slot, released when it finishes."""
    try:
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
    finally:
        _render_slots.release()


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
            job_id = db.create_release_image_job(edition_id, g.user_id, dyno=os.environ.get('DYNO'))
            if job_id is None:
                return jsonify({'error': 'Images are already rendering for this edition.'}), 409
            if not _render_slots.acquire(blocking=False):
                db.finish_release_image_job(job_id, error='Image rendering is busy right now. Try again in a minute.')
                return jsonify({'error': 'Image rendering is busy right now. Try again in a minute.'}), 429
            job = db.get_latest_release_image_job(edition_id)

        try:
            threading.Thread(
                target=_run_render_job,
                args=(job_id, edition, UserImageLibraries.for_card_build(g.user_id), source_card_ids),
                name=f'release-images-{job_id[:8]}', daemon=True,
            ).start()
        except Exception as exc:
            # The worker releases the slot itself, so it's only ours to release if it never started
            _render_slots.release()
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
