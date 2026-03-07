import v1.uploaded.modules.marchir as marchir_util
import config_validator as config

async def run_marker(page, marker_results):
    print("Colour Contrast Marker")

    return {
        'Colour Contrast Error Count': 0,
        'Contrast Ratios': 0
    } 