import type { ReactNode, RefObject } from 'react';
import { FaPlus, FaSpinner, FaStar } from 'react-icons/fa6';
import type { PublicReleaseSort, Release, ReleaseCollection } from '../../api/releases';
import type { CommunityReleases } from './useCommunityReleases';
import type { ReleaseLibrary } from './useReleaseLibrary';
import { ReleaseItem, ReleaseItemSkeleton, NewReleaseTile } from './ReleaseItem';
import { ReleaseGuideButton } from './ReleaseGuide';
import { TeamSearchInput } from '../team_builder/TeamSearchInput';
import { TeamShelf } from '../team_builder/TeamShelf';
import { choiceClass } from '../shared/choiceStyles';
import { InlineError } from '../shared/InlineError';
import { RetryableError } from '../shared/RetryableError';
import { Heading } from '../shared/Heading';
import { BetaBadge } from '../shared/BetaBadge';
import { buttonClass } from '../shared/buttonStyles';
import { EmptyState } from '../shared/EmptyState';
import { SignInPrompt } from '../shared/SignInPrompt';
import { PinstripeBackdrop } from '../shared/PinstripeBackdrop';
import { PageSubtitle } from '../shared/PageSubtitle';
import { SectionBand } from '../shared/SectionBand';

/** Phones get a 44px minimum touch target on small controls; wider screens keep their normal size. */
const TOUCH_TARGET = 'max-sm:min-h-11';

/** Release tiles: two per row on phones, fixed-width tiles that wrap on wider screens. */
const RELEASE_GRID = 'grid grid-cols-2 sm:flex sm:flex-wrap gap-3';

/** UX spacing — matches TeamBuilder */
const PX = 'px-4 sm:px-8';

const COMMUNITY_SORTS: { value: PublicReleaseSort; label: string }[] = [
    { value: 'popular', label: 'Popular' },
    { value: 'new', label: 'New' },
];

type ReleaseListProps = {
    listRef: RefObject<HTMLDivElement | null>;
    signedIn: boolean;
    library: ReleaseLibrary;
    community: CommunityReleases;
    /** Why the list opened in place of a release link. */
    notice: string | null;
    onOpen: (release: Release, readOnly: boolean) => void;
    onOpenCommunity: (release: Release) => void;
    onCreate: () => void;
    onOpenGuide: () => void;
};

/** The Release Builder's landing page: the viewer's library (their own, saved and official
 *  releases) over every community release. */
export function ReleaseList({ listRef, signedIn, library, community, notice, onOpen, onOpenCommunity, onCreate, onOpenGuide }: ReleaseListProps) {
    const officialShelves = officialShelvesFor(library.official, library.collections);
    return (
        <div ref={listRef} className="@container w-full relative isolate">
            {/* Card-back pinstripes behind the page header, echoing the release tiles' card fields */}
            <PinstripeBackdrop heightClass="h-72" />
            <div className="flex flex-col gap-6 py-4 max-w-4xl lg:max-w-7xl mx-auto w-full">
                <div className={`flex items-center gap-3 ${PX} justify-between`}>
                    <div className="min-w-0">
                        {/* One line on phones: the title shrinks to fit beside the buttons instead of wrapping */}
                        <div className="flex items-center gap-2 min-w-0">
                            <Heading level="page" fit>Release Builder</Heading>
                            <BetaBadge className="shrink-0" />
                        </div>
                        <PageSubtitle>
                            Browse official card sets or build your own
                        </PageSubtitle>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                        <ReleaseGuideButton onClick={onOpenGuide} className={TOUCH_TARGET} />
                        {signedIn && (
                            <button type="button" onClick={onCreate} className={buttonClass('primary', 'sm', TOUCH_TARGET)}>
                                <FaPlus className="text-[10px]" />
                                <span>New<span className="hidden sm:inline"> release</span></span>
                            </button>
                        )}
                    </div>
                </div>

                {notice && (
                    <div className={PX}>
                        <InlineError size="md">{notice}</InlineError>
                    </div>
                )}

                {library.error && (
                    <div className={PX}>
                        <RetryableError onRetry={library.reload}>{library.error}</RetryableError>
                    </div>
                )}

                {/* Skeleton only until this viewer's lists first load; a reload keeps the tiles up, dimmed */}
                {library.loading && !library.ready ? (
                    <section className={PX}>
                        <div className="h-3 w-24 rounded-plate bg-(--background-tertiary) animate-pulse mb-2" />
                        <ReleaseSkeletonRow />
                    </section>
                ) : (
                    <>
                        {/* Signed out, the invite to build takes My Releases' place at the top */}
                        {!signedIn && (
                            <div className={PX}>
                                <SignInPrompt
                                    size="panel"
                                    title="Build your own release."
                                    message="Sign in to create your own releases, save others' and like your favorites."
                                />
                            </div>
                        )}

                        {/* Each section only as wide as its tiles, so short lists share a row and longer ones wrap onto their own */}
                        <div className={`${PX} flex flex-col gap-6 sm:flex-row sm:flex-wrap sm:gap-x-12 sm:items-start ${library.loading ? 'opacity-60' : ''} transition-opacity`}>
                            {signedIn && (
                                <ReleaseSection title="My Releases" releases={library.mine} onOpen={r => onOpen(r, false)} showPublishStatus>
                                    {/* Also the empty state when the user has no releases yet */}
                                    <NewReleaseTile onClick={onCreate} />
                                </ReleaseSection>
                            )}
                            {/* Other users' releases whose cards the user searches in the Card Explorer */}
                            {library.saved.length > 0 && (
                                <ReleaseSection title="Saved" releases={library.saved} onOpen={r => onOpen(r, true)} />
                            )}
                        </div>

                        {/* Official releases on a band of their own, every group a carousel: one per collection with the
                            description the admin wrote under its title, then any the admin hasn't grouped */}
                        {officialShelves.length > 0 && (
                            <SectionBand
                                tone="bg-(--background-secondary)"
                                accent="--challenge-legendary"
                                icon={<FaStar />}
                                title="Official"
                                description="Card sets from the creator of Showdown Bot."
                                horizontalPadding={PX}
                            >
                                {officialShelves.map(({ key, title, description, releases }) => (
                                    <TeamShelf
                                        key={key}
                                        title={title}
                                        subtitle={description ?? undefined}
                                        wrapSubtitle
                                        headingLevel="panel"
                                        className={PX}
                                        bleed
                                    >
                                        {releases.map(release => (
                                            <div key={release.id} className="shrink-0 w-44 sm:w-52">
                                                <ReleaseItem release={release} onClick={() => onOpen(release, true)} />
                                            </div>
                                        ))}
                                    </TeamShelf>
                                ))}
                            </SectionBand>
                        )}
                    </>
                )}

                <CommunitySection community={community} onOpen={onOpenCommunity} />
            </div>
        </div>
    );
}

type OfficialShelf = { key: string; title: string; description: string | null; releases: Release[] };

/** The official releases as shelves: one per visible collection that has any (collections in their admin
 *  order, releases by their place in it, then newest first as loaded), then a last shelf of the ones in no
 *  collection, called plain "Releases" when there are no collections at all. */
function officialShelvesFor(official: Release[], collections: ReleaseCollection[]): OfficialShelf[] {
    const shelves: OfficialShelf[] = collections
        .map(collection => ({
            key: collection.slug,
            title: collection.title,
            description: collection.description,
            releases: official
                .filter(r => r.collection_slug === collection.slug)
                .sort((a, b) => (a.collection_sort_index ?? 1e9) - (b.collection_sort_index ?? 1e9)),
        }))
        .filter(shelf => shelf.releases.length > 0);
    const grouped = new Set(shelves.map(shelf => shelf.key));
    const rest = official.filter(r => !r.collection_slug || !grouped.has(r.collection_slug));
    if (rest.length > 0) {
        shelves.push({ key: '__ungrouped', title: shelves.length > 0 ? 'More releases' : 'Releases', description: null, releases: rest });
    }
    return shelves;
}

type ReleaseSectionProps = {
    title: string;
    releases: Release[];
    onOpen: (release: Release) => void;
    showPublishStatus?: boolean;
    /** Tiles after the releases, such as the New release tile. */
    children?: ReactNode;
};

/** A titled library section of release tiles. */
function ReleaseSection({ title, releases, onOpen, showPublishStatus, children }: ReleaseSectionProps) {
    return (
        <section className="min-w-0">
            <Heading level="section" as="h2" className="mb-3">{title}</Heading>
            <div className={RELEASE_GRID}>
                {releases.map(release => (
                    <ReleaseItem key={release.id} release={release} onClick={() => onOpen(release)} showPublishStatus={showPublishStatus} />
                ))}
                {children}
            </div>
        </section>
    );
}

/** Every listed community release, the user's own included: sorted and searched on the server, a page at a time. */
function CommunitySection({ community, onOpen }: { community: CommunityReleases; onOpen: (release: Release) => void }) {
    const { releases, loading, hasMore, error, loadMore, sort, setSort, search, setSearch, searching } = community;
    return (
        <section className={`${PX} flex flex-col gap-3`}>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                <Heading level="section" as="h2">Community</Heading>
                <div className="flex gap-2 sm:gap-1.5" role="group" aria-label="Sort community releases">
                    {COMMUNITY_SORTS.map(option => (
                        <button
                            key={option.value}
                            type="button"
                            aria-pressed={sort === option.value}
                            onClick={() => setSort(option.value)}
                            className={choiceClass(sort === option.value, 'sm', TOUCH_TARGET)}
                        >
                            {option.label}
                        </button>
                    ))}
                </div>
                <TeamSearchInput
                    value={search}
                    onChange={setSearch}
                    placeholder="Search by name or creator…"
                    className="w-full sm:w-72 sm:ml-auto"
                />
            </div>

            {error && <InlineError size="md">{error}</InlineError>}

            {releases === null ? (
                <ReleaseSkeletonRow />
            ) : releases.length === 0 ? (
                searching ? (
                    <EmptyState size="inline">No releases match “{search.trim()}”.</EmptyState>
                ) : (
                    <EmptyState size="panel" title="No community releases yet.">
                        Publish one of your releases and it shows up here.
                    </EmptyState>
                )
            ) : (
                <>
                    <div className={`${RELEASE_GRID} ${loading ? 'opacity-60' : ''} transition-opacity`}>
                        {releases.map(release => (
                            <ReleaseItem key={release.id} release={release} onClick={() => onOpen(release)} />
                        ))}
                    </div>
                    {hasMore && (
                        <button type="button" onClick={loadMore} disabled={loading} className={buttonClass('secondary', 'md', `self-center ${TOUCH_TARGET}`)}>
                            {loading && <FaSpinner className="animate-spin text-[11px]" />} Load more
                        </button>
                    )}
                </>
            )}
        </section>
    );
}

/** A single row of tile skeletons: two on phones; on wider screens the row is clipped to one tile
 *  height (sm:w-52 at 3/4 aspect), so tiles that would wrap stay hidden. */
function ReleaseSkeletonRow() {
    return (
        <div className={`${RELEASE_GRID} sm:h-[calc(13rem*4/3)] sm:overflow-hidden`}>
            {Array.from({ length: 8 }, (_, i) => (
                <div key={i} className={i >= 2 ? 'max-sm:hidden' : undefined}>
                    <ReleaseItemSkeleton />
                </div>
            ))}
        </div>
    );
}
