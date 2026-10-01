from playwright.async_api import Page

import config_marker as config
import v1.uploaded.modules.marchir as marchir_util


def get_distances_within_section(section_title, input_boxes, result):
    distances = []
    for index, (upper, lower) in enumerate(zip(input_boxes, input_boxes[1:])):
        distance = abs(lower["y"] - (upper["y"] + upper["height"]))
        distances.append(distance)
        result[f"{section_title}{index}"] = distance
    return distances


def get_average_distance(distances):
    return abs(sum(distances) / len(distances)) if distances else 0


def get_distances_between_sections(sections, result):
    distances = []
    for index, (upper, lower) in enumerate(zip(sections, sections[1:])):
        last_input = upper["inputs"][-1]
        first_input = lower["inputs"][0]
        distance = abs(first_input["y"] - (last_input["y"] + last_input["height"]))
        distances.append(distance)
        result[f"section{index}"] = distance
    return distances


def get_minimum_distance_between_sections(distances):
    return min(distances) if distances else 0


def deduct_mark(result, mark_to_deduct):
    result["Proximity-mark"] = max(0, result["Proximity-mark"] - mark_to_deduct)


async def is_section_title_visible(section_container, section_title):
    expected_title = section_title.replace("-", "").lower()
    elements = await marchir_util.get_elements_with_css_selector(section_container, "*")
    for element in elements:
        if not await element.is_visible():
            continue
        text = await marchir_util.get_text(element)
        if text and "".join(text.split()).lower() == expected_title:
            return True
    return False


def finalize_result(result):
    result["proximityPenalties"] = ";".join(result["proximityPenalties"])
    result["flags"] = ";".join(result["flags"])
    return result


async def run_marker(page: Page, marker_results):
    """Score section spacing from 0 to 2 using the supplied browser page."""
    result = {"Proximity-mark": 2, "proximityPenalties": [], "flags": []}
    form_container = page.locator(f"#{config.form_id}").first

    # Other markers share this page and may already have opened the popup.
    if not await form_container.is_visible():
        try:
            trigger = await marchir_util.wait_for_clickable_element_with_id(
                page, config.popup_button_to_click_id
            )
            await trigger.click(timeout=10000)
        except Exception:
            deduct_mark(result, 2)
            result["proximityPenalties"].append(
                f"Can't click element id={config.popup_button_to_click_id}"
            )
            return finalize_result(result)

    try:
        form_container = await marchir_util.wait_for_visible_element_with_id(
            page, config.form_id, 50000
        )
    except Exception:
        deduct_mark(result, 2)
        result["proximityPenalties"].append(f"Can't find visible id={config.form_id}")
        return finalize_result(result)

    found_sections = []
    average_distances_within_sections = []
    for section_title in config.form_sections:
        section = await marchir_util.get_element_with_css_selector(
            form_container, f"#{section_title}"
        )
        section_box = await section.bounding_box() if section is not None else None
        if section_box is None:
            deduct_mark(result, 1)
            result["proximityPenalties"].append(f"Can't find {section_title} section")
            continue

        inputs = await marchir_util.get_elements_with_css_selector(section, "input")
        input_boxes = []
        for element in inputs:
            box = await element.bounding_box()
            if box is not None:
                input_boxes.append(box)
        if not input_boxes:
            deduct_mark(result, 1)
            result["proximityPenalties"].append(f"Can't find {section_title} section elements")
            continue

        # Keep DOM input order, as in the original marker; sort sections visually below.
        found_sections.append({"y": section_box["y"], "inputs": input_boxes})
        if await is_section_title_visible(section, section_title):
            result["flags"].append(f"The section {section_title} does not fully rely on proximity.")
        distances = get_distances_within_section(section_title, input_boxes, result)
        average_distances_within_sections.append(get_average_distance(distances))

    average_within = get_average_distance(average_distances_within_sections)
    if not found_sections:
        deduct_mark(result, 1)
        result["proximityPenalties"].append("No sections found")
        return finalize_result(result)
    if len(found_sections) < 2:
        deduct_mark(result, 1)
        result["proximityPenalties"].append("Only one section in the form")
        return finalize_result(result)

    found_sections.sort(key=lambda section: section["y"])
    distances_between = get_distances_between_sections(found_sections, result)
    average_between = get_average_distance(distances_between)
    minimum_between = get_minimum_distance_between_sections(distances_between)

    if average_within == 0 and average_between == 0:
        deduct_mark(result, 2)
        result["proximityPenalties"].append("Distance within and between groups is 0")
    if average_within > average_between:
        deduct_mark(result, 1)
        result["proximityPenalties"].append("Average distance between groups is less than or equal to average distance within groups")
    if average_within > minimum_between:
        deduct_mark(result, 1)
        result["proximityPenalties"].append("Minimum distance between groups is less than or equal to average distance within groups")
    if average_between > 1000:
        deduct_mark(result, 1)
        result["proximityPenalties"].append("Malformed group structure")

    return finalize_result(result)
