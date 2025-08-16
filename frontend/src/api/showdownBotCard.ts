const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";

// Generic type for api
type Primitive = string | number | boolean | null | undefined;

/** Sends the entire form (minus File) as JSON to /build_custom_card */
export async function buildCustomCard(payload: Record<string, Primitive>) : Promise<ShowdownBotCardAPIResponse> {
    
    // Image is sent separately, so we remove it from the payload
    const { image_upload, image_source, ...cleaned_data } = payload;

    // Fetch the API endpoint
    const res = await fetch(`${API_BASE}/build_custom_card`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cleaned_data),
    });

    // Handle errors
    if (!res.ok) throw new Error(`Build failed: ${res.status}`);

    // Convert to ShowdownBotCardAPIResponse
    return res.json();
}

// MARK: - Showdown Bot Card Types

export type ShowdownBotCardAPIResponse = {
    card: ShowdownBotCard | null;
    error: string | null;
    error_for_user: string | null;
};

export type ShowdownBotCard = {
    name: string;
    year: string | number;
    image: ShowdownBotCardImage;
}

type ShowdownBotCardImage = {
    output_file_name: string;
    output_folder_path: string;
};