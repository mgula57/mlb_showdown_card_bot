"""In-app notifications for signed-in users: what other people (and their sims) did that concerns them.

Routes call a `Notifier` after the action they notify about has been saved. Notifying is best-effort:
a failure is logged and never fails the request. Nobody is notified about their own actions, or about
a group they've turned off (`NotificationPreferences`). Each new notification pings its recipient's
Realtime channel so an open bell refreshes at once.

The frontend words each `NotificationKind` (`frontend/src/api/notifications.ts`), so adding a kind means
adding it here and there.
"""

import traceback
from enum import Enum
from functools import wraps
from typing import Iterable, Optional

from ..database.postgres_db import PostgresDB
from ..supabase.realtime_broadcast import RealtimeBroadcaster


class NotificationGroup(str, Enum):
    """What a user can turn off on the Account page. Matches `NOTIFICATION_GROUPS` in the frontend."""
    COMMENTS = 'comments'
    REMIXES = 'remixes'
    LEAGUES = 'leagues'
    GAMES = 'games'
    LOBBIES = 'lobbies'


class NotificationKind(str, Enum):
    # Someone replied to your comment
    COMMENT_REPLY = 'comment_reply'
    # Someone commented on your release or team (a reply in one of its threads too)
    SUBJECT_COMMENT = 'subject_comment'
    # Someone remixed your release
    RELEASE_REMIX = 'release_remix'
    # Someone joined your league (commissioner)
    LEAGUE_JOIN = 'league_join'
    # The commissioner started a draft (members)
    LEAGUE_DRAFT_START = 'league_draft_start'
    # It's your pick. At most one unread per league, and making a pick marks it read
    LEAGUE_ON_THE_CLOCK = 'league_on_the_clock'
    # The commissioner removed you from a league
    LEAGUE_REMOVED = 'league_removed'
    # A season's regular season is over (members)
    LEAGUE_REGULAR_SEASON_END = 'league_regular_season_end'
    # A season is over (members)
    LEAGUE_SEASON_COMPLETE = 'league_season_complete'
    # Someone took the open seat in your live game
    LIVE_GAME_ACCEPTED = 'live_game_accepted'
    # A live game you play in is final
    LIVE_GAME_FINAL = 'live_game_final'
    # Someone claimed a club in your sim lobby (host)
    LOBBY_JOIN = 'lobby_join'
    # The host started a sim lobby you're in (members)
    LOBBY_START = 'lobby_start'
    # A sim lobby's season finished (host and members)
    LOBBY_FINISHED = 'lobby_finished'

    @property
    def group(self) -> NotificationGroup:
        return _KIND_GROUPS[self]


_KIND_GROUPS: dict[NotificationKind, NotificationGroup] = {
    NotificationKind.COMMENT_REPLY: NotificationGroup.COMMENTS,
    NotificationKind.SUBJECT_COMMENT: NotificationGroup.COMMENTS,
    NotificationKind.RELEASE_REMIX: NotificationGroup.REMIXES,
    NotificationKind.LEAGUE_JOIN: NotificationGroup.LEAGUES,
    NotificationKind.LEAGUE_DRAFT_START: NotificationGroup.LEAGUES,
    NotificationKind.LEAGUE_ON_THE_CLOCK: NotificationGroup.LEAGUES,
    NotificationKind.LEAGUE_REMOVED: NotificationGroup.LEAGUES,
    NotificationKind.LEAGUE_REGULAR_SEASON_END: NotificationGroup.LEAGUES,
    NotificationKind.LEAGUE_SEASON_COMPLETE: NotificationGroup.LEAGUES,
    NotificationKind.LIVE_GAME_ACCEPTED: NotificationGroup.GAMES,
    NotificationKind.LIVE_GAME_FINAL: NotificationGroup.GAMES,
    NotificationKind.LOBBY_JOIN: NotificationGroup.LOBBIES,
    NotificationKind.LOBBY_START: NotificationGroup.LOBBIES,
    NotificationKind.LOBBY_FINISHED: NotificationGroup.LOBBIES,
}
assert set(_KIND_GROUPS) == set(NotificationKind)


class NotificationPreferences:
    """A user's `notification_prefs`: `{group: false}` for each group they've turned off. Everything is on
    until turned off, so a user who never saved any gets every notification."""

    @staticmethod
    def clean(raw) -> Optional[dict[str, bool]]:
        """The known groups' on/off values from a settings payload, or None if it isn't an object."""
        if not isinstance(raw, dict):
            return None
        return {group.value: raw[group.value] for group in NotificationGroup if isinstance(raw.get(group.value), bool)}

    @staticmethod
    def allows(prefs: Optional[dict], kind: NotificationKind) -> bool:
        return (prefs or {}).get(kind.group.value) is not False


def _best_effort(method):
    @wraps(method)
    def wrapped(*args, **kwargs) -> None:
        try:
            method(*args, **kwargs)
        except Exception:
            traceback.print_exc()
    return wrapped


def _humans(user_ids: Iterable[Optional[str]]) -> list[str]:
    """The distinct real users among `user_ids` (bot and sim seats have none)."""
    return list(dict.fromkeys(user_id for user_id in user_ids if user_id))


class Notifier:
    """Records notifications through an open `PostgresDB`."""

    def __init__(self, db: PostgresDB) -> None:
        self.db = db

    # MARK: Comments and releases

    @_best_effort
    def comment_posted(self, comment: dict, owner_id: Optional[str]) -> None:
        """A comment (as `PostgresDB.create_comment` returns it) on a subject `owner_id` owns. The person
        it replied to hears about it as a reply; the owner hears about it once, unless it replied to them."""
        recipients: dict[str, NotificationKind] = {}
        if comment.get('parent_id'):
            reply_target = self.db.get_comment_reply_target(comment['id'])
            if reply_target:
                recipients[reply_target] = NotificationKind.COMMENT_REPLY
        if owner_id:
            recipients.setdefault(owner_id, NotificationKind.SUBJECT_COMMENT)
        self._send(comment['user_id'], comment['subject_type'], comment['subject_id'], recipients, comment_id=comment['id'])

    @_best_effort
    def release_remixed(self, source_release: dict, remixer_id: str) -> None:
        """`remixer_id` started a remix of `source_release`. Points at the source, since the remix is
        the remixer's own until they publish it."""
        owner_id = source_release.get('created_by')
        if owner_id:
            self._send(remixer_id, 'release', str(source_release['id']), {owner_id: NotificationKind.RELEASE_REMIX})

    # MARK: Leagues

    @_best_effort
    def league_joined(self, league: dict, user_id: str) -> None:
        self._send_league(league, user_id, [league['commissioner_user_id']], NotificationKind.LEAGUE_JOIN)

    @_best_effort
    def league_member_removed(self, league: dict, removed_user_id: Optional[str], actor_id: str) -> None:
        """Only when someone else removed them; leaving on your own isn't news to you."""
        if removed_user_id and removed_user_id != actor_id:
            self._send_league(league, actor_id, [removed_user_id], NotificationKind.LEAGUE_REMOVED)

    @_best_effort
    def league_draft_started(self, league: dict, members: list[dict], actor_id: str) -> None:
        self._send_league(league, actor_id, [m.get('user_id') for m in members], NotificationKind.LEAGUE_DRAFT_START)

    @_best_effort
    def league_draft_advanced(self, league: dict, picker_id: str, on_the_clock: Optional[dict]) -> None:
        """After a pick (and any bot picks after it): everyone else's "on the clock" is done, and whoever
        is up now hears about it, unless they already have an unread one for this league."""
        up_next = on_the_clock.get('user_id') if on_the_clock else None
        self.db.mark_stale_notifications_read(NotificationKind.LEAGUE_ON_THE_CLOCK.value, 'league', str(league['league_id']), up_next)
        if up_next:
            self._send_league(league, picker_id, [up_next], NotificationKind.LEAGUE_ON_THE_CLOCK, skip_if_unread=True)

    @_best_effort
    def league_season_advanced(self, league: dict, members: list[dict], status_before: str, status_after: str) -> None:
        """A sim chunk moved a season on: the regular season ended, or the whole season did. The sim did it,
        so the commissioner who pressed play hears about it too."""
        if status_after == status_before:
            return
        if status_after == 'complete':
            kind = NotificationKind.LEAGUE_SEASON_COMPLETE
        elif status_after == 'postseason':
            kind = NotificationKind.LEAGUE_REGULAR_SEASON_END
        else:
            return
        self._send_league(league, None, [m.get('user_id') for m in members], kind)

    def _send_league(self, league: dict, actor_id: Optional[str], user_ids: Iterable[Optional[str]], kind: NotificationKind,
                     skip_if_unread: bool = False) -> None:
        self._send(actor_id, 'league', str(league['league_id']), {user_id: kind for user_id in _humans(user_ids)},
                   skip_if_unread=skip_if_unread)

    # MARK: Live games

    @_best_effort
    def live_game_accepted(self, game: dict, accepter_id: str) -> None:
        self._send(accepter_id, 'live_game', str(game['live_game_id']),
                   {game['created_by']: NotificationKind.LIVE_GAME_ACCEPTED})

    @_best_effort
    def live_game_final(self, game: dict, actor_id: Optional[str]) -> None:
        """Both seats' players hear it's over, except whoever made the final play (they saw it)."""
        players = _humans([game.get('away_user_id'), game.get('home_user_id')])
        self._send(actor_id, 'live_game', str(game['live_game_id']), {user_id: NotificationKind.LIVE_GAME_FINAL for user_id in players})

    # MARK: Sim lobbies

    @_best_effort
    def lobby_joined(self, lobby: dict, user_id: str) -> None:
        self._send(user_id, 'sim_lobby', str(lobby['lobby_id']), {lobby['host_user_id']: NotificationKind.LOBBY_JOIN})

    @_best_effort
    def lobby_started(self, lobby: dict, members: list[dict]) -> None:
        self._send(lobby['host_user_id'], 'sim_lobby', str(lobby['lobby_id']),
                   {user_id: NotificationKind.LOBBY_START for user_id in _humans(m.get('user_id') for m in members)})

    @_best_effort
    def sim_job_finished(self, job_id: str) -> None:
        """A sim job succeeded. If it was a lobby's season, its host and members hear about it."""
        lobby = self.db.get_sim_lobby_by_job(job_id)
        if lobby is None:
            return
        members = self.db.get_sim_lobby_members(lobby['lobby_id'])
        players = _humans([lobby['host_user_id'], *(m.get('user_id') for m in members)])
        self._send(None, 'sim_lobby', lobby['lobby_id'], {user_id: NotificationKind.LOBBY_FINISHED for user_id in players})

    # MARK: Sending

    def _send(self, actor_id: Optional[str], subject_type: str, subject_id: str, recipients: dict[str, NotificationKind],
              comment_id: Optional[str] = None, skip_if_unread: bool = False) -> None:
        recipients = {user_id: kind for user_id, kind in recipients.items() if user_id and user_id != actor_id}
        if not recipients:
            return
        prefs = self.db.get_notification_prefs(list(recipients))
        rows = [
            {
                'user_id': user_id, 'kind': kind.value, 'actor_id': actor_id,
                'subject_type': subject_type, 'subject_id': subject_id, 'comment_id': comment_id,
            }
            for user_id, kind in recipients.items() if NotificationPreferences.allows(prefs.get(user_id), kind)
        ]
        notified = self.db.create_notifications(rows, skip_if_unread=skip_if_unread)
        RealtimeBroadcaster().notifications_changed(notified)
