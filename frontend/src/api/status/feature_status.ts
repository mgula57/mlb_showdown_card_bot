
const API_BASE = import.meta.env.PROD ? "/api" : "http://127.0.0.1:5000/api";
/**
 * Tab/Feature status interface
 */
export interface FeatureStatus {
    feature_name: string;
    is_disabled: boolean;
    message: string | null;
    updated_at: string | null;
}

/**
 * Fetches feature statuses from the API
 * 
 * @returns Promise resolving to a record of feature statuses
 * @throws Error if API request fails
 **/
export const fetchFeatureStatuses = async (): Promise<Record<string, FeatureStatus>> => {
    
    // Fetch from API
    try {
        const response = await fetch(`${API_BASE}/feature_status`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data: Record<string, FeatureStatus> = await response.json();
        
        return data;
    } catch (error) {
        console.error('Error fetching feature statuses:', error);
        return {};
    }
};