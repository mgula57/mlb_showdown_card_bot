/**
 * @fileoverview Seasons page Transactions tab: the offseason's trades and free-agent moves leading
 * into an upcoming season, each player with his card from the year before in the user's set, plus
 * every club's net change in card points.
 */
import { useEffect, useState } from "react";
import { FaXmark } from "react-icons/fa6";

import { fetchSeasonTransactions, type TransactionFeed, type TransactionMove, type TransactionMoveKind } from "../../api/mlbAPI";
import { useFullCardResponse, type CardSelection } from "../../hooks/useFullCardResponse";
import { CardDetail } from "../cards/CardDetail";
import { CarouselRow } from "../shared/CarouselRow";
import CustomSelect from "../shared/CustomSelect";
import { EmptyState } from "../shared/EmptyState";
import { Eyebrow } from "../shared/Eyebrow";
import { Heading } from "../shared/Heading";
import { Modal } from "../shared/Modal";
import { Plate } from "../shared/Plate";
import { RetryableError } from "../shared/RetryableError";
import { SearchInput } from "../shared/SearchInput";
import { TeamChip } from "../shared/TeamChip";
import { buttonClass } from "../shared/buttonStyles";
import { choiceClass } from "../shared/choiceStyles";
import { CAPS_LABEL_CLASS } from "../shared/fieldStyles";
import { MoveKindIcon, TransactionMoveItem, TransactionMoveItemSkeleton } from "./TransactionMoveItem";
import { feedTeamIdentity, formatMoveDate, formatMoveDay, groupByDay, moveMatchesSearch } from "./transactionMoves";

const PAGE_SIZE = 20;
const ALL_TEAMS = "all";

type KindFilter = "all" | TransactionMoveKind;

const KIND_FILTERS: { id: KindFilter; label: string }[] = [
    { id: "all", label: "All" },
    { id: "trade", label: "Trades" },
    { id: "signing", label: "Signings" },
    { id: "free_agent", label: "Free agents" },
    { id: "waiver_claim", label: "Claims" },
];

/** Net card points, signed. */
const formatNet = (net: number): string => (net > 0 ? `+${net}` : `${net}`);
const netClass = (net: number): string => (net > 0 ? "text-(--green)" : net < 0 ? "text-(--red)" : "text-(--text-tertiary)");

type TransactionsProps = {
    seasonId: string;
    showdownSet: string;
    /** Fetches only once the tab is first shown. */
    isActive: boolean;
};

export default function Transactions({ seasonId, showdownSet, isActive }: TransactionsProps) {
    const [reloadCount, setReloadCount] = useState(0);
    // The last finished request, tagged with what it asked for. Loading is derived from the tag
    // not matching the current request, so the effect only sets state once the fetch settles.
    const requestKey = `${seasonId}:${showdownSet}:${reloadCount}`;
    const [result, setResult] = useState<{ key: string; feed: TransactionFeed | null; error: string | null } | null>(null);

    const [kindFilter, setKindFilter] = useState<KindFilter>("all");
    const [teamFilter, setTeamFilter] = useState<string>(ALL_TEAMS);
    const [search, setSearch] = useState("");
    // How many moves are shown, for the filters it was set under. A new filter starts on page one.
    const filterKey = `${kindFilter}:${teamFilter}:${search}:${requestKey}`;
    const [page, setPage] = useState({ key: filterKey, count: PAGE_SIZE });
    const visibleCount = page.key === filterKey ? page.count : PAGE_SIZE;
    const [selectedCard, setSelectedCard] = useState<CardSelection | null>(null);
    const modalCard = useFullCardResponse(selectedCard, "transactions");

    useEffect(() => {
        if (!isActive) return;
        const controller = new AbortController();
        fetchSeasonTransactions(seasonId, { showdownSet }, controller.signal)
            .then((feed) => setResult({ key: requestKey, feed, error: null }))
            .catch((err) => {
                if (err instanceof Error && err.name === "AbortError") return;
                setResult({ key: requestKey, feed: null, error: "Couldn't load transactions. Try again." });
            });
        return () => controller.abort();
    }, [seasonId, showdownSet, isActive, requestKey]);

    const isLoading = result?.key !== requestKey;
    const feed = isLoading ? null : result?.feed ?? null;
    const error = isLoading ? null : result?.error ?? null;

    const teamId = teamFilter === ALL_TEAMS ? null : Number(teamFilter);
    const teams = feed?.teams ?? {};
    // The team filter and the search both narrow every list (and the kind chips' counts); the kind
    // filter applies last, so each chip shows how many moves it would leave.
    const isShown = (move: TransactionMove) =>
        (teamId === null || move.team_ids.includes(teamId)) && moveMatchesSearch(move, search, teams);

    const teamMoves = (feed?.moves ?? []).filter(isShown);
    const moves = kindFilter === "all" ? teamMoves : teamMoves.filter((move) => move.kind === kindFilter);
    const otherMoves = (feed?.other_moves ?? []).filter(isShown);
    // Each day's full count under the current filters, so a day cut off by "Show more" still reads true
    const movesPerDay: { [date: string]: number } = {};
    for (const move of moves) movesPerDay[move.date ?? ""] = (movesPerDay[move.date ?? ""] ?? 0) + 1;
    const kindCounts: { [kind: string]: number } = { all: teamMoves.length };
    for (const move of teamMoves) kindCounts[move.kind] = (kindCounts[move.kind] ?? 0) + 1;

    const teamOptions = [
        { value: ALL_TEAMS, label: "All teams" },
        ...Object.values(teams)
            .sort((a, b) => (a.abbreviation || "").localeCompare(b.abbreviation || ""))
            .map((team) => ({ value: String(team.id), label: team.name || team.abbreviation || String(team.id) })),
    ];
    const teamChange = teamId !== null ? feed?.team_changes.find((change) => change.team_id === teamId) : undefined;
    const priorYear = Number(seasonId) - 1;

    if (error) {
        return (
            <div className="px-3 lg:px-0 lg:pt-6 lg:pr-6 pb-24">
                <RetryableError onRetry={() => setReloadCount((count) => count + 1)}>{error}</RetryableError>
            </div>
        );
    }

    return (
        <div className="px-3 lg:px-0 lg:pt-6 lg:pr-6 pb-24 space-y-5">
            <div className="space-y-1">
                <Heading level="section" as="h2">Transactions</Heading>
                <p className="text-xs text-(--text-secondary)">
                    Trades and free agency from the {seasonId} offseason. Players show their {feed?.card_year ?? priorYear} cards in your set.
                </p>
            </div>

            {/* Filters. The chips grow to fill their line, so the search and team picker sit at the
                right beside them and start at the left once they wrap under. */}
            <div className="flex flex-wrap items-center gap-2">
                <div className="grow flex flex-wrap gap-1.5">
                    {KIND_FILTERS.map((filter) => (
                        <button
                            key={filter.id}
                            type="button"
                            onClick={() => setKindFilter(filter.id)}
                            className={choiceClass(kindFilter === filter.id, "sm")}
                        >
                            {filter.id !== "all" && <MoveKindIcon kind={filter.id} className="h-3 w-3 shrink-0 text-(--text-tertiary)" />}
                            {filter.label}
                            {feed && <span className="tabular-nums text-(--text-tertiary)">{kindCounts[filter.id] ?? 0}</span>}
                        </button>
                    ))}
                </div>
                <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
                    <SearchInput
                        value={search}
                        onChange={setSearch}
                        placeholder="Search players or teams"
                        className="w-full sm:w-56"
                    />
                    <CustomSelect
                        value={teamFilter}
                        onChange={setTeamFilter}
                        options={teamOptions}
                        size="sm"
                        prefix="Team"
                        className="w-full sm:w-56"
                    />
                </div>
            </div>

            {/* Net change: every club ranked. Picking one filters to it (the same filter as the Team
                dropdown) and keeps the row in place, with the club outlined; picking it again, or
                "Show all teams", clears it. The picked club's ins and outs show under the row. */}
            {feed && feed.team_changes.length > 0 && (
                <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2 min-h-7">
                        <Eyebrow>Net change in mlb card points</Eyebrow>
                        {teamId !== null && (
                            <button type="button" onClick={() => setTeamFilter(ALL_TEAMS)} className={buttonClass("ghost", "sm")}>
                                <FaXmark className="h-3 w-3" aria-hidden />
                                Show all teams
                            </button>
                        )}
                    </div>
                    <CarouselRow gutter="seasonsTab" className="gap-2! py-0.5">
                        {feed.team_changes.map((change) => {
                            const team = teams[String(change.team_id)];
                            if (!team) return null;
                            const isSelected = change.team_id === teamId;
                            return (
                                <button
                                    key={change.team_id}
                                    type="button"
                                    aria-pressed={isSelected}
                                    onClick={() => setTeamFilter(isSelected ? ALL_TEAMS : String(change.team_id))}
                                    className={`shrink-0 flex items-center gap-2 rounded-card border bg-(--background-secondary) px-2.5 py-1.5 transition-colors cursor-pointer ${
                                        isSelected
                                            ? "border-(--showdown-blue) ring-1 ring-(--showdown-blue)"
                                            : "border-(--divider) hover:border-(--rule-strong)"
                                    }`}
                                    title={isSelected ? "Show all teams" : `${change.players_in} in, ${change.players_out} out`}
                                >
                                    <TeamChip team={feedTeamIdentity(team)} size="sm" />
                                    <span className={`font-display-upright text-[15px] leading-none tabular-nums ${netClass(change.net)}`}>{formatNet(change.net)}</span>
                                </button>
                            );
                        })}
                    </CarouselRow>
                    {teamChange && (
                        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 rounded-card border border-(--divider) bg-(--background-secondary) px-4 py-3">
                            {[
                                { label: `In (${teamChange.players_in})`, value: `+${teamChange.points_in}`, className: "text-(--green)" },
                                { label: `Out (${teamChange.players_out})`, value: `-${teamChange.points_out}`, className: "text-(--red)" },
                                { label: "Net", value: formatNet(teamChange.net), className: netClass(teamChange.net) },
                            ].map((stat) => (
                                <div key={stat.label} className="flex flex-col gap-1">
                                    <span className={`${CAPS_LABEL_CLASS} text-(--text-tertiary)`}>{stat.label}</span>
                                    <span className={`font-display-upright text-xl leading-none tabular-nums ${stat.className}`}>{stat.value}</span>
                                </div>
                            ))}
                            <span className="text-xs text-(--text-tertiary) sm:ml-auto">Card points gained and lost this offseason.</span>
                        </div>
                    )}
                </div>
            )}

            {/* Moves */}
            {isLoading ? (
                <div className="grid gap-3 xl:grid-cols-2">
                    {[...Array(4)].map((_, i) => <TransactionMoveItemSkeleton key={i} />)}
                </div>
            ) : feed && !feed.window_start ? (
                <EmptyState size="panel" title="Hot stove opens soon.">
                    Moves show up here once the {seasonId} offseason begins.
                </EmptyState>
            ) : moves.length === 0 && search.trim() ? (
                <EmptyState size="panel" title="No matching moves.">
                    Nothing matches "{search.trim()}"{kindFilter !== "all" || teamId !== null ? " with these filters" : ""}.
                </EmptyState>
            ) : moves.length === 0 ? (
                <EmptyState size="panel" title="No moves yet.">
                    Nothing here with a {feed?.card_year ?? priorYear} card yet. Check back as the offseason heats up.
                </EmptyState>
            ) : (
                <div className="space-y-5">
                    {/* One section per day, newest first: an eyebrow and count over a hairline, then that
                        day's moves in the grid. A day cut off by "Show more" picks up after it. */}
                    {groupByDay(moves.slice(0, visibleCount)).map((day) => (
                        <section key={day.date} className="space-y-3">
                            <div className="flex items-baseline gap-2 pb-1.5 border-b border-(--divider)">
                                <Eyebrow>{formatMoveDay(day.date)}</Eyebrow>
                                <span className="text-[11px] tabular-nums text-(--text-tertiary)">
                                    {movesPerDay[day.date]} {movesPerDay[day.date] === 1 ? "move" : "moves"}
                                </span>
                            </div>
                            <div className="grid gap-3 lg:grid-cols-2 xl:grid-cols-3 items-start">
                                {day.moves.map((move) => (
                                    <TransactionMoveItem
                                        key={move.id}
                                        move={move}
                                        teams={teams}
                                        cardYear={feed!.card_year}
                                        onCardSelect={(card, cardId) => setSelectedCard({ card, cardId })}
                                        hideDate
                                    />
                                ))}
                            </div>
                        </section>
                    ))}
                    {moves.length > visibleCount && (
                        <div className="flex justify-center">
                            <button type="button" onClick={() => setPage({ key: filterKey, count: visibleCount + PAGE_SIZE })} className={buttonClass("secondary", "sm")}>
                                Show more ({moves.length - visibleCount})
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Moves where nobody has a card */}
            {otherMoves.length > 0 && kindFilter === "all" && (
                <div className="space-y-2">
                    <Eyebrow>Other moves</Eyebrow>
                    <p className="text-xs text-(--text-tertiary)">Major-league moves for players without a {feed?.card_year ?? priorYear} card.</p>
                    <ul className="rounded-card border border-(--divider) bg-(--background-secondary) divide-y divide-(--divider)">
                        {otherMoves.map((move) => (
                            <li key={move.id} className="flex items-start gap-3 px-3 py-2 text-xs">
                                <span className="w-12 shrink-0 tabular-nums text-(--text-tertiary)">{formatMoveDate(move.date)}</span>
                                <span className="text-(--text-secondary)">{move.description}</span>
                                {move.kind === "trade" && <Plate size="xs" variant="outline" className="ml-auto shrink-0">Trade</Plate>}
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            <div className={selectedCard ? "" : "hidden pointer-events-none"}>
                <Modal onClose={() => setSelectedCard(null)} isVisible={!!selectedCard} size="xl">
                    <CardDetail
                        showdownBotCardData={modalCard.data}
                        isLoading={modalCard.isLoading}
                        hideTrendGraphs={true}
                        context="home"
                        parent="home"
                    />
                </Modal>
            </div>
        </div>
    );
}
