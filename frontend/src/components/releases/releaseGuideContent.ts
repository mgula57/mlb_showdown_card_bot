import { RELEASE_TIP_COPY } from './releaseOnboardingState';

/** The guide's sections, in build order. `setup` and `pool` share their ids with EditionBuilder's steps;
 *  `images` is the Player Pool's Images tab. */
export const RELEASE_GUIDE_SECTIONS = ['plan', 'setup', 'pool', 'images', 'publish'] as const;
export type ReleaseGuideSectionId = typeof RELEASE_GUIDE_SECTIONS[number];

export type ReleaseGuideTip = { title: string; body: string };

/** `step` is the Edition Builder step bar's number for the section (Images is a tab inside step 2); null for Plan. */
export const RELEASE_GUIDE: Record<ReleaseGuideSectionId, { label: string; title: string; step: number | null; tips: ReleaseGuideTip[] }> = {
    plan: {
        label: 'Plan',
        step: null,
        title: 'Plan your release',
        tips: [
            {
                title: 'One release, several editions',
                body: 'A release is your card set; editions are the sub-sets inside it, like a Base Set plus a Trading Deadline follow-up. Each edition has its own setup, pool, style and images.',
            },
            {
                title: 'Start from a template',
                body: "The WOTC base set templates match an original set's position mix, average points and share of low point cards. Take that as a starting point to match the original set characteristics and distribution. Adjusting one is quicker than starting from Custom.",
            },
            {
                title: 'Work in private',
                body: 'Nothing is public until you publish. Use Preview to see the release the way others will.',
            },
        ],
    },
    setup: {
        label: 'Setup',
        step: 1,
        title: 'Setup',
        tips: [
            {
                title: 'Settle the scope first',
                body: 'Establish the size, showdown sets, and years used. Changing them later flags cards already in the pool that fall outside the new scope.',
            },
            {
                title: 'Adjust the default stats period used',
                body: 'The algorithm picks players on full-season stats by default. Choose to use a different period if needed, for example a half-season for a TD or PR set.',
            },
        ],
    },
    pool: {
        label: 'Pool',
        step: 2,
        title: 'Player Pool',
        tips: [
            RELEASE_TIP_COPY.buildMethod,
            RELEASE_TIP_COPY.savePreview,
            {
                title: 'Check who just missed',
                body: "The Cutoff tab shows the players just below the line. Add one from Manual search to always include them, or remove a card from the pool to keep that player out of future runs.",
            },
            {
                title: 'Tune priorities, not just minimums',
                body: 'Minimums decide who is eligible; the priority weights (Quality, Volume, Teams, PTS Fit, Career) decide who gets picked first. Change those to shift the feel of the set.',
            },
            {
                title: 'Suggest foils last',
                body: 'Suggest foils picks about 15% of the saved pool, counting cards you already tagged. Run it once the pool is settled; you review every pick before anything is tagged. NOTE: foil tagging does not actually effect card design itself.',
            },
        ],
    },
    images: {
        label: 'Images',
        step: 2,
        title: 'Images',
        tips: [
            RELEASE_TIP_COPY.imageLibraries,
            RELEASE_TIP_COPY.cardStyle,
            {
                title: 'Style rules for the exceptions',
                body: 'Card Style rules restyle every card that matches a condition, so a group of cards can get a different look without editing each one. Later rules win, and a card\'s own style edits win over rules.',
            },
            RELEASE_TIP_COPY.render,
        ],
    },
    publish: {
        label: 'Publish',
        step: 3,
        title: 'Review & Publish',
        tips: [
            RELEASE_TIP_COPY.publish,
            {
                title: 'Must fix comes first',
                body: 'Must fix items block publishing. Check and Polish items are suggestions, so decide which ones matter for your set.',
            },
            {
                title: 'Publish just for yourself',
                body: 'Set Who can find it to Only me to lock in a version for your own teams and card search without sharing it. You can open it up later; the link stays the same.',
            },
            {
                title: 'Allow remixes',
                body: 'Others can start their own release from yours, and theirs credits yours.',
            },
            {
                title: 'Still adding cards?',
                body: 'Mark the release as work in progress so people know more cards or changes are coming.',
            },
        ],
    },
};
