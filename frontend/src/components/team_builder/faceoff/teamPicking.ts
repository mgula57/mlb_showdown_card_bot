/**
 * @fileoverview Which teams can take the field in a game against another team (a Faceoff or a live
 * game), and their starters.
 */
import { ROTATION_ROLES, type Team, type TeamSummary } from '../../../api/userTeams';

/** A finished team the sim can field: not mid-draft, not archived, and one a user or the site built. */
export const isPlayable = (team: TeamSummary) => !team.is_drafting && !team.is_archived && (team.source === 'user' || team.source === 'official');

/** The team's starters, in rotation order. */
export const rotationOf = (team: Team | null) => (team?.rotation ?? []).filter(r => (ROTATION_ROLES as readonly string[]).includes(r.role));
