import { useState } from 'react';
import { CustomSelect } from '../shared/CustomSelect';
import { FaTable, FaPoll, FaCoins } from 'react-icons/fa';
import { type ShowdownBotCardAPIResponse } from '../../api/showdownBotCard';

// Images
import blankPlayer2001Dark from '../../assets/blankplayer-2001-dark.png';

// Tables
import { TableRealVsProjected } from './TableRealVsProjectedBreakdown';
import { TableChartsBreakdown } from './TableChartsBreakdown';
import { TablePointsBreakdown } from './TablePointsBreakdown';

/** Type for CardDetail inputs */
type CardDetailProps = {
    showdownBotCardData: ShowdownBotCardAPIResponse | null;
};

/** Shows Showdown Bot Card Details. Used in Custom card form and modals throughout UI */
export function CardDetail({ showdownBotCardData }: CardDetailProps) {

    // Breakdown State
    const [breakdownType, setBreakdownType] = useState<string>("Stats");

    // Card Calcs
    const cardImagePath: string | null = showdownBotCardData?.card?.image ? `${showdownBotCardData.card.image.output_folder_path}/${showdownBotCardData.card.image.output_file_name}` : null;

    const renderBlankPlayerImageName = () => {
        return blankPlayer2001Dark;
    }

    const renderBreakdownTable = () => {
        switch (breakdownType) {
            case 'Stats':
                return (
                    <div className='space-y-2 overflow-y-auto'>
                        <TableRealVsProjected
                            realVsProjectedData={showdownBotCardData?.card?.real_vs_projected_stats || []}
                        />

                        {/* Footnote */}
                        <div className='flex flex-col text-xs leading-tight space-y-2'>
                            <i>* Indicates a Bot estimated value, real stat unavailable (ex: 1800's, Negro Leagues, PU/FB/GB)</i>
                            <i>** Chart category was adjusted in post-processing to increase accuracy</i>
                        </div>

                    </div>
                );
            case 'Points':
                return (
                    <div className='space-y-2 overflow-y-auto'>

                        <TablePointsBreakdown
                            pointsBreakdownData={showdownBotCardData?.card?.points_breakdown || null}
                            ip={showdownBotCardData?.card?.ip || null}
                        />

                        {/* Footnote */}
                        <div className='text-xs leading-tight'>
                            <i>* Slashlines and HR projections used for points are based on Steroid Era opponent.
                                Stats may not match projections against player's era.</i>
                        </div>

                    </div>
                );
            case 'Charts':
                return (
                    <TableChartsBreakdown
                        chartAccuracyData={showdownBotCardData?.card?.command_out_accuracy_breakdowns || {}}
                    />
                );
        }
    }

    const breakdownFirstRowHeight = 'lg:h-[500px] xl:h-[600px]';

    return (
        <div 
            className="
                w-full
                bg-background-secondary
                overflow-y-auto
                p-4 space-y-6
                h-full
                pb-24
            "
        >
            {/* Image and Breakdown Tables */}
                <div
                    className={`
                        flex flex-col lg:flex-row
                        lg:items-start
                        ${breakdownFirstRowHeight}
                        gap-4
                    `}
                >
                    {/* Card Image */}
                    <img
                        src={cardImagePath == null ? renderBlankPlayerImageName() : cardImagePath}
                        alt="Blank Player"
                        className={`
                            block w-auto h-auto mx-auto
                            ${breakdownFirstRowHeight}
                            rounded-xl
                            object-contain
                            shadow-2xl
                            `}
                    />

                    {/* Card Tables */}
                    <div
                        className={`
                            flex flex-col
                            w-full lg:max-w-128
                            bg-secondary
                            p-4 rounded-xl
                            space-y-4
                            ${breakdownFirstRowHeight}
                        `}
                    >
                        <CustomSelect
                            value={breakdownType}
                            options={[
                                { label: 'Card vs Real Stats', value: 'Stats', icon: <FaPoll /> },
                                { label: 'Points', value: 'Points', icon: <FaCoins /> },
                                { label: 'Chart', value: 'Charts', icon: <FaTable /> }
                            ]}
                            onChange={(value) => setBreakdownType(value)}
                        />

                        {/* Breakdown Table */}
                        {renderBreakdownTable()}

                    </div>

                </div>

        </div>
    );
}