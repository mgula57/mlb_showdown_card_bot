/**
 * @fileoverview TeamHierarchy - Hierarchical team selection component
 * 
 * Provides a three-tier selection system for filtering cards by organizational structure:
 * Organization → League → Team, with dynamic filtering at each level.
 */

import { useMemo } from 'react';
import MultiSelect from '../shared/MultiSelect';
import type { TeamHierarchyRecord } from '../../api/card_db/cardDatabase';

/**
 * Props for the TeamHierarchy component
 */
interface TeamHierarchyProps {
    /** Complete hierarchy data from the database */
    hierarchyData: TeamHierarchyRecord[];
    /** Currently selected organizations */
    selectedOrganizations?: string[];
    /** Currently selected leagues */
    selectedLeagues?: string[];
    /** Currently selected teams */
    selectedTeams?: string[];
    /** Handler for organization selection changes */
    onOrganizationChange: (values: string[]) => void;
    /** Handler for league selection changes */
    onLeagueChange: (values: string[]) => void;
    /** Handler for team selection changes */
    onTeamChange: (values: string[]) => void;
    /** Disable organization selector */
    disableOrganization?: boolean;
    /** Disable league selector */
    disableLeague?: boolean;
    /** Disable team selector */
    disableTeam?: boolean;
}

/**
 * TeamHierarchy - Hierarchical team selection component
 * 
 * Provides cascading filters for baseball organizational structure:
 * 
 * **Organization Level**: MLB, Negro Leagues, etc.
 * **League Level**: AL, NL, Eastern League, etc. (filtered by organization)
 * **Team Level**: Individual teams (filtered by organization + league)
 * 
 * Each level dynamically updates based on higher-level selections,
 * ensuring users can only select valid combinations that exist in the data.
 * 
 * @param hierarchyData - Complete team hierarchy from database
 * @param selectedOrganizations - Current organization selections
 * @param selectedLeagues - Current league selections  
 * @param selectedTeams - Current team selections
 * @param onOrganizationChange - Organization change handler
 * @param onLeagueChange - League change handler
 * @param onTeamChange - Team change handler
 * 
 * @example
 * ```tsx
 * <TeamHierarchy
 *   hierarchyData={teamData}
 *   selectedOrganizations={filters.organization}
 *   selectedLeagues={filters.league}
 *   selectedTeams={filters.team}
 *   onOrganizationChange={(orgs) => updateFilters({organization: orgs})}
 *   onLeagueChange={(leagues) => updateFilters({league: leagues})}
 *   onTeamChange={(teams) => updateFilters({team: teams})}
 * />
 * ```
 */
export const TeamHierarchy: React.FC<TeamHierarchyProps> = ({
    hierarchyData,
    selectedOrganizations = [],
    selectedLeagues = [],
    selectedTeams = [],
    onOrganizationChange,
    onLeagueChange,
    onTeamChange,
    disableOrganization = false,
    disableLeague = false,
    disableTeam = false,
}) => {
    /**
     * Generate organization options from hierarchy data
     * All unique organizations sorted alphabetically
     */
    const organizationOptions: { value: string; label: string }[] = useMemo(() => {
        const uniqueOrgs = [...new Set(hierarchyData.map(item => item.organization))];
        return uniqueOrgs
            .sort()
            .map(org => ({ value: org, label: org }));
    }, [hierarchyData]);

    /**
     * Generate league options filtered by selected organizations
     * Only shows leagues that exist within the selected organizations
     */
    const leagueOptions: { value: string; label: string }[] = useMemo(() => {
        let filteredData = hierarchyData;
        
        // Filter by selected organizations if any are selected
        if (selectedOrganizations.length > 0) {
            filteredData = hierarchyData.filter(item => 
                selectedOrganizations.includes(item.organization)
            );
        }
        
        const uniqueLeagues = [...new Set(filteredData.map(item => item.league))];
        return uniqueLeagues
            .sort()
            .map(league => ({ value: league, label: league }));
    }, [hierarchyData, selectedOrganizations]);

    /**
     * Generate team options filtered by selected organizations and leagues
     * Only shows teams that exist within the selected org/league combinations
     */
    const teamOptions: { value: string; label: string }[] = useMemo(() => {
        let filteredData = hierarchyData;
        
        if (selectedOrganizations.length > 0) {
            filteredData = filteredData.filter(item => 
                selectedOrganizations.includes(item.organization)
            );
        }
        
        if (selectedLeagues.length > 0) {
            filteredData = filteredData.filter(item => 
                selectedLeagues.includes(item.league)
            );
        }
        
        const uniqueTeams = [...new Set(filteredData.map(item => item.team))];
        return uniqueTeams
            .sort()
            .map(team => ({ value: team, label: team }));
    }, [hierarchyData, selectedOrganizations, selectedLeagues]);

    // Handle changes and clear invalid selections
    const handleOrganizationChange = (values: string[]) => {
        onOrganizationChange(values);
        
        // Clear invalid leagues and teams
        if (values.length > 0) {
            const validLeagues = [...new Set(
                hierarchyData
                    .filter(item => values.includes(item.organization))
                    .map(item => item.league)
            )];
            const filteredLeagues = selectedLeagues.filter(league => validLeagues.includes(league));
            if (filteredLeagues.length !== selectedLeagues.length) {
                onLeagueChange(filteredLeagues);
            }

            const validTeams = [...new Set(
                hierarchyData
                    .filter(item => values.includes(item.organization) && 
                                   (filteredLeagues.length === 0 || filteredLeagues.includes(item.league)))
                    .map(item => item.team)
            )];
            const filteredTeams = selectedTeams.filter(team => validTeams.includes(team));
            if (filteredTeams.length !== selectedTeams.length) {
                onTeamChange(filteredTeams);
            }
        }
    };

    const handleLeagueChange = (values: string[]) => {
        onLeagueChange(values);
        
        // Clear invalid teams
        if (values.length > 0 || selectedOrganizations.length > 0) {
            let validTeamsData = hierarchyData;
            
            if (selectedOrganizations.length > 0) {
                validTeamsData = validTeamsData.filter(item => 
                    selectedOrganizations.includes(item.organization)
                );
            }
            
            if (values.length > 0) {
                validTeamsData = validTeamsData.filter(item => 
                    values.includes(item.league)
                );
            }
            
            const validTeams = [...new Set(validTeamsData.map(item => item.team))];
            const filteredTeams = selectedTeams.filter(team => validTeams.includes(team));
            if (filteredTeams.length !== selectedTeams.length) {
                onTeamChange(filteredTeams);
            }
        }
    };

    return (
        <>
            <MultiSelect
                label="Organizations"
                options={organizationOptions}
                selections={selectedOrganizations}
                onChange={handleOrganizationChange}
                disabled={disableOrganization}
            />

            <MultiSelect
                label="Leagues"
                options={leagueOptions}
                selections={selectedLeagues}
                onChange={handleLeagueChange}
                disabled={disableLeague}
            />

            <MultiSelect
                label="Teams"
                options={teamOptions}
                selections={selectedTeams}
                onChange={onTeamChange}
                disabled={disableTeam}
            />
        </>
    );
};