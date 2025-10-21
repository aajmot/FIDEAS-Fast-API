"""
Utility functions for migrating from CTkComboBox to SearchableDropdown
"""
from core.shared.components.searchable_dropdown import SearchableDropdown

def create_searchable_dropdown(parent, values=None, command=None, width=200, height=28, 
                             placeholder_text="Search...", allow_add_new=False, **kwargs):
    """
    Create a SearchableDropdown with consistent styling
    
    Args:
        parent: Parent widget
        values: List of dropdown values
        command: Callback function when value is selected
        width: Width of the dropdown
        height: Height of the dropdown
        placeholder_text: Placeholder text for search
        allow_add_new: Allow adding new values
        **kwargs: Additional arguments
    
    Returns:
        SearchableDropdown instance
    """
    return SearchableDropdown(
        parent=parent,
        values=values or [],
        command=command,
        width=width,
        height=height,
        placeholder_text=placeholder_text,
        allow_add_new=allow_add_new,
        **kwargs
    )

def migrate_combobox_values(combobox_values):
    """
    Convert CTkComboBox values format to SearchableDropdown format
    
    Args:
        combobox_values: List of values from CTkComboBox
    
    Returns:
        List of values compatible with SearchableDropdown
    """
    if not combobox_values:
        return []
    
    # Handle both simple strings and "id:name" format
    processed_values = []
    for value in combobox_values:
        if isinstance(value, str):
            processed_values.append(value)
        else:
            processed_values.append(str(value))
    
    return processed_values

def extract_id_from_value(value):
    """
    Extract ID from "id:name" format value
    
    Args:
        value: String in "id:name" format
    
    Returns:
        ID part of the value or None
    """
    if not value or ':' not in value:
        return None
    
    try:
        return int(value.split(':')[0])
    except (ValueError, IndexError):
        return None

def extract_name_from_value(value):
    """
    Extract name from "id:name" format value
    
    Args:
        value: String in "id:name" format
    
    Returns:
        Name part of the value or the original value
    """
    if not value or ':' not in value:
        return value
    
    try:
        return value.split(':', 1)[1]
    except IndexError:
        return value