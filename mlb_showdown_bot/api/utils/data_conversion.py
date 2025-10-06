
def convert_form_data_types(form_data: dict) -> dict:
    """Convert form data strings back to appropriate types"""
    
    # Define expected types for each field
    BOOLEAN_FIELDS = {'is_dark_mode', 'is_bordered', 'hide_team_logo', 
                     'add_one_to_set_year', 'show_year_text', 'is_variable_speed_00_01'}
    INTEGER_FIELDS = {'year', 'chart_version', 'image_glow_multiplier'}
    
    converted = {}
    
    for key, value in form_data.items():
        if key == 'image_upload':
            converted[key] = value  # Keep file data as-is
            continue
            
        # Handle null/empty values
        if value == 'null' or value == '':
            converted[key] = None
            continue
            
        # Convert based on field type
        if key in BOOLEAN_FIELDS:
            converted[key] = value.lower() == 'true'
        elif key in INTEGER_FIELDS:
            try:
                converted[key] = int(value)
            except ValueError:
                converted[key] = value  # Keep as string if conversion fails
        else:
            converted[key] = value  # Keep as string
    
    return converted