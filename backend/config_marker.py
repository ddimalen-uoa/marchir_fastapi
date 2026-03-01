import v1.uploaded.project_markers as project_markers
from v1.uploaded.project_markers import *

# Dictionary of Marker Functions
# marker_functions = {
#     'pop_up_marker': project_markers.pop_up_marker.run_marker,
#     'common_fate_marker': project_markers.common_fate_marker.run_marker,
#     'custom_colour_marker': project_markers.custom_colour_marker.run_marker,
#     'accessibility_marker': project_markers.accessibility_marker.run_marker,
#     'proximity_marker': project_markers.proximity_marker.run_marker,
#     'colour_contrast_marker': project_markers.colour_contrast_marker.run_marker      
# }

# CustomColourMarker Configurations
custom_color_class = ".custom-colour"
custom_background_color_class = ".custom-background-colour"
custom_border_color_class = ".custom-border-colour"

# Dictionary of border styles to accept, and their corresponding acceptable width
border_styles = {'dotted': 3, 'dashed':3, 'solid': 3, 'double': 3}

# PopUpMarker Configuration
popup_button_to_click_id = "trigger-modal"
form_id = "form-ct"

# Fitts law labels
fitts_origin = 'fitts-input-field'
fitts_end = 'fitts-submit-button'

# A list of section names in the form 
# A section name should be connected using '-', because the proximity marker needs to get original section titles from this list and it assumes the section title is connected using '-'. 
form_sections = ["user-details", "address-details", "contact-details"]