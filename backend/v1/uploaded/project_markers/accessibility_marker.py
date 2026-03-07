import v1.uploaded.modules.marchir as marchir_util
import config_validator as config

async def run_marker(page, marker_results):
    print("Accessiblity Marker")

    return {
        'Accessibility Error Count': 0,
        'Accessibility Errors': 0,
        'Accessibility Flags':0,
        'Alt Text Found': 0,
        'Alt Text Word Counts': 0
    } 