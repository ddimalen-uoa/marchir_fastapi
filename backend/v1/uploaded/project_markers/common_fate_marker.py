import v1.uploaded.modules.marchir as marchir_util
import config_marker as config


def most_frequent_coor(arr: list[float]) -> float:
    if not arr:
        return 0

    counts = {}
    for value in arr:
        counts[value] = counts.get(value, 0) + 1

    max_count = 0
    key = arr[0]

    for value, count in counts.items():
        if count > max_count:
            max_count = count
            key = value

    return key


def second_most_frequent_coor(most_frequent: float, arr: list[float]) -> float:
    new_arr = [x for x in arr if x != most_frequent]
    return most_frequent_coor(new_arr)


async def get_element_x_coordinate(element) -> float | None:
    try:
        box = await element.bounding_box()
        if box is None:
            return None
        return box["x"]
    except Exception:
        return None


async def get_element_display_text(element) -> str | None:
    try:
        text = await marchir_util.get_text(element)
        if text:
            return text

        placeholder = await marchir_util.get_attribute(element, "placeholder")
        if placeholder:
            stripped = placeholder.strip()
            return stripped if stripped else None

        return None
    except Exception:
        return None


async def aligned_percentage(most_frequent_coor_value: float, elements: list) -> int:
    if not elements:
        return 0

    aligned_elements = []

    for element in elements:
        x_coord = await get_element_x_coordinate(element)
        if x_coord is None:
            continue

        if x_coord == most_frequent_coor_value:
            text = await get_element_display_text(element)
            aligned_elements.append(text if text else "")

    return round(len(aligned_elements) / len(elements) * 100)


async def run_marker(page, marker_results):
    out_dict = {
        "Input-field Common Fate": 0,
        "Input-field Common Fate Penalties": "",
        "Label Common Fate": 0,
        "Label Common Fate Penalties": "",
    }

    try:
        trigger_button = await marchir_util.wait_for_clickable_element_with_id(
            page,
            config.popup_button_to_click_id,
        )
    except Exception:
        out_dict["Input-field Common Fate"] = 0
        out_dict["Input-field Common Fate Penalties"] = (
            f"Popup failed to open form using {config.popup_button_to_click_id}"
        )
        out_dict["Label Common Fate"] = 0
        out_dict["Label Common Fate Penalties"] = (
            f"Popup failed to open form using {config.popup_button_to_click_id}"
        )
        return out_dict

    try:
        await marchir_util.click_element(trigger_button)
    except Exception:
        out_dict["Input-field Common Fate"] = 0
        out_dict["Input-field Common Fate Penalties"] = (
            f"Popup failed to open form using {config.popup_button_to_click_id}"
        )
        out_dict["Label Common Fate"] = 0
        out_dict["Label Common Fate Penalties"] = (
            f"Popup failed to open form using {config.popup_button_to_click_id}"
        )
        return out_dict

    try:
        main_container = await marchir_util.wait_for_visible_element_with_id(
            page,
            config.form_id,
            50,
        )
    except Exception:
        message = (
            f"Can't find {config.form_id} or Popup failed to open form using "
            f"{config.popup_button_to_click_id}"
        )
        out_dict["Input-field Common Fate"] = 0
        out_dict["Input-field Common Fate Penalties"] = message
        out_dict["Label Common Fate"] = 0
        out_dict["Label Common Fate Penalties"] = message
        return out_dict

    inputs = await marchir_util.get_elements_with_css_selector(main_container, "input")
    labels = await marchir_util.get_elements_with_css_selector(main_container, "label")

    inp_coor: list[float] = []
    lab_coor: list[float] = []

    visible_inputs = []
    visible_labels = []

    for question in inputs:
        x_absolute_coord = await get_element_x_coordinate(question)
        if x_absolute_coord is not None:
            inp_coor.append(x_absolute_coord)
            visible_inputs.append(question)

    for label in labels:
        x_absolute_coord = await get_element_x_coordinate(label)
        if x_absolute_coord is not None:
            lab_coor.append(x_absolute_coord)
            visible_labels.append(label)

    # Calculating Common Fate for input fields
    if len(inp_coor) > 0:
        inp_most_frequent_coor = most_frequent_coor(inp_coor)
        total_results = await aligned_percentage(inp_most_frequent_coor, visible_inputs)

        out_dict["Input-field Common Fate"] = total_results
        if total_results == 0:
            out_dict["Input-field Common Fate Penalties"] = (
                "Elements are not properly aligned or two column layouts not yet supported."
            )
        else:
            out_dict["Input-field Common Fate Penalties"] = ""
    else:
        out_dict["Input-field Common Fate"] = 0
        out_dict["Input-field Common Fate Penalties"] = "Could not find input elements"

    # Calculating Common Fate for labels
    if len(lab_coor) > 0:
        lab_most_frequent_coor = most_frequent_coor(lab_coor)
        total_results = await aligned_percentage(lab_most_frequent_coor, visible_labels)

        out_dict["Label Common Fate"] = total_results
        if total_results == 0:
            out_dict["Label Common Fate Penalties"] = (
                "Elements are not properly aligned or two column layouts not yet supported."
            )
        else:
            out_dict["Label Common Fate Penalties"] = ""
    else:
        out_dict["Label Common Fate"] = 0
        out_dict["Label Common Fate Penalties"] = "Could not find label elements"

    return out_dict