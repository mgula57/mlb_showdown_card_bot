import { useMemo } from 'react';
import MultiSelect from '../shared/MultiSelect';
import type { TeamHierarchyRecord } from '../../api/card_db/cardDatabase';

interface TeamHierarchyProps {
    hierarchyData: TeamHierarchyRecord[];
    selectedOrganizations?: string[];
    selectedLeagues?: string[];
    selectedTeams?: string[];
    onOrganizationChange: (values: string[]) => void;
    onLeagueChange: (values: string[]) => void;
    onTeamChange: (values: string[]) => void;
}

export const TeamHierarchy: React.FC<TeamHierarchyProps> = ({
    hierarchyData,
    selectedOrganizations = [],
    selectedLeagues = [],
    selectedTeams = [],
    onOrganizationChange,
    onLeagueChange,
    onTeamChange,
}) => {
    // Get unique organizations
    const organizationOptions: { value: string; label: string }[] = useMemo(() => {
        const uniqueOrgs = [...new Set(hierarchyData.map(item => item.organization))];
        return uniqueOrgs
            .sort()
            .map(org => ({ value: org, label: org }));
    }, [hierarchyData]);

    // Get leagues filtered by selected organizations
    const leagueOptions: { value: string; label: string }[] = useMemo(() => {
        let filteredData = hierarchyData;
        
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

    // Get teams filtered by selected organizations and leagues
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
            />

            <MultiSelect
                label="Leagues"
                options={leagueOptions}
                selections={selectedLeagues}
                onChange={handleLeagueChange}
            />

            <MultiSelect
                label="Teams"
                options={teamOptions}
                selections={selectedTeams}
                onChange={onTeamChange}
            />
        </>
    );
};