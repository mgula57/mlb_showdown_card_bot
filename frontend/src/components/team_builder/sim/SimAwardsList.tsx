import { FaTrophy } from 'react-icons/fa6';
import type { AwardWinner, SimTeamIdentity } from '../../../api/sim';
import CardIdentityCell from '../../cards/card_elements/CardIdentityCell';
import { CardDetail } from '../../cards/CardDetail';
import { Modal } from '../../shared/Modal';
import { useCardLinks } from './useCardLinks';

const AWARD_LABELS: Record<AwardWinner['category'], string> = {
    MVP: 'MVP',
    CY_YOUNG: 'Cy Young',
    ROY: 'Rookie of the Year',
    SILVER_SLUGGER: 'Silver Slugger',
};

type Props = {
    awardsByLeague: [string, AwardWinner[]][];
    /** Schedule key -> branding (`SeasonSimSummary.identities`) — see `SimStatsTable`'s prop of
     * the same name. A winner's sim-team colors win over their card's own archived colors. */
    identities?: Record<string, SimTeamIdentity>;
};

/** Award winners, one section per league, each row linked to its real Showdown card. */
export function SimAwardsList({ awardsByLeague, identities }: Props) {
    const players = awardsByLeague.flatMap(([, awards]) => awards.map(a => a.player));
    const { recordFor, isLoadingCard, selected, open, close, isFetching } = useCardLinks(players, true);

    return (
        <div className="flex flex-col gap-5">
            {awardsByLeague.map(([league, awards]) => (
                <div key={league}>
                    <p className="text-[12px] font-bold text-(--text-primary) mb-1">{league}</p>
                    <div className="flex flex-col gap-1.5">
                        {awards.map((award, i) => {
                            const record = recordFor(award.player);
                            const clickable = !!record;
                            const teamIdentity = identities?.[award.player.team ?? ''];
                            return (
                                <div
                                    key={i}
                                    onClick={clickable ? () => open(record!.card_id, record!.source) : undefined}
                                    className={`flex items-center gap-2 text-[12px] rounded-lg bg-(--background-tertiary) px-3 py-2 ${clickable ? 'cursor-pointer hover:bg-(--background-quaternary)' : ''}`}
                                >
                                    <FaTrophy className="text-(--secondary) shrink-0" />
                                    <span className="font-bold text-(--text-primary) w-40 shrink-0">
                                        {AWARD_LABELS[award.category]}{award.position ? ` (${award.position})` : ''}
                                    </span>
                                    <CardIdentityCell
                                        name={award.player.name} hasCard={!!record}
                                        isLoadingCard={isLoadingCard(award.player) || (record ? isFetching(record.card_id) : false)}
                                        isPitcher={record?.is_pitcher}
                                        primaryColor={teamIdentity?.primary_color ?? record?.color_primary}
                                        secondaryColor={teamIdentity?.secondary_color ?? record?.color_secondary}
                                        command={record?.command} team={award.player.team} points={record?.points}
                                    />
                                    <span className="text-(--text-tertiary)">{award.player.team}</span>
                                    <span className="ml-auto text-(--text-tertiary)">{award.value_label}</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            ))}
            <div className={selected ? '' : 'hidden pointer-events-none'}>
                <Modal onClose={close} isVisible={!!selected}>
                    <CardDetail showdownBotCardData={selected} hideTrendGraphs={true} context="sim_result" parent="sim_result" />
                </Modal>
            </div>
        </div>
    );
}
