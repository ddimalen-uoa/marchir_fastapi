import v1.uploaded.modules.marchir as marchir_util
import config_validator as config

def calculate_luminance(rgb: str) -> float:
    """
    rgb is expected in the format: 'rgb(r, g, b)'
    """
    rgb_values = [float(val.strip()) for val in rgb[4:-1].split(",")]
    r, g, b = rgb_values

    r_normalized = r / 255.0
    g_normalized = g / 255.0
    b_normalized = b / 255.0

    r_srgb = (
        r_normalized / 12.92
        if r_normalized <= 0.03928
        else ((r_normalized + 0.055) / 1.055) ** 2.4
    )
    g_srgb = (
        g_normalized / 12.92
        if g_normalized <= 0.03928
        else ((g_normalized + 0.055) / 1.055) ** 2.4
    )
    b_srgb = (
        b_normalized / 12.92
        if b_normalized <= 0.03928
        else ((b_normalized + 0.055) / 1.055) ** 2.4
    )

    return 0.2126 * r_srgb + 0.7152 * g_srgb + 0.0722 * b_srgb


def get_contrast_ratio(colour1: str, colour2: str) -> float:
    lum1 = calculate_luminance(colour1)
    lum2 = calculate_luminance(colour2)
    ratio = (lum1 + 0.05) / (lum2 + 0.05)
    return round(max(ratio, 1 / ratio), 2)


def parse_rgba(colour: str) -> tuple[float, float, float, float]:
    """
    Supports:
    - rgba(r, g, b, a)
    - rgb(r, g, b)  -> alpha defaults to 1.0
    """
    colour = colour.strip()

    if colour.startswith("rgba("):
        values = [float(val.strip()) for val in colour[5:-1].split(",")]
        r, g, b, a = values
        return r, g, b, a

    if colour.startswith("rgb("):
        values = [float(val.strip()) for val in colour[4:-1].split(",")]
        r, g, b = values
        return r, g, b, 1.0

    raise ValueError(f"Unsupported colour format: {colour}")


def rgba_to_rgb_string(colour: str) -> str:
    r, g, b, _ = parse_rgba(colour)
    return f"rgb({int(r)}, {int(g)}, {int(b)})"


def has_transparency(colour: str) -> bool:
    _, _, _, a = parse_rgba(colour)
    return a < 1.0


def has_invisible_background(colour: str) -> bool:
    _, _, _, a = parse_rgba(colour)
    return a == 0.0

async def get_true_text(element) -> str | None:
    """
    Gets only the direct text nodes of the element, not descendant text.
    This is much faster and more accurate than subtracting child inner_text.
    """
    try:
        return await element.evaluate("""
            (el) => {
                let text = '';
                for (const node of el.childNodes) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        text += node.textContent || '';
                    }
                }
                text = text.trim();
                return text || null;
            }
        """)
    except Exception:
        return None
    
async def is_element_and_ancestors_visible(element):
    while element is not None:
        if not await marchir_util.is_displayed(element):
            return False

        tag_name = await marchir_util.get_tag_name(element)
        element = ( 
            await marchir_util.get_element_with_xpath(element, "..") 
            if tag_name != "html" 
            else None 
        )

    return True

async def has_background_image(element) -> bool:
    bg_colour = await marchir_util.get_css_property(element, "background-color")
    bg_image = await marchir_util.get_css_property(element, "background-image")

    if bg_image and bg_image != "none":
        return True

    while has_invisible_background(bg_colour):
        try:
            parent_element = await marchir_util.get_element_with_xpath(element, "..")
            if parent_element is None:
                break

            parent_tag = await marchir_util.get_tag_name(parent_element)
            if parent_tag == "html":
                break

            bg_image = await marchir_util.get_css_property(
                parent_element, "background-image"
            )
            if bg_image and bg_image != "none":
                return True

            bg_colour = await marchir_util.get_css_property(
                parent_element, "background-color"
            )
            element = parent_element
        except Exception:
            break

    return False

async def get_effective_background_colour(element) -> str:
    bg_colour = await marchir_util.get_css_property(element, "background-color")

    while has_invisible_background(bg_colour):
        try:
            parent_element = await marchir_util.get_element_with_xpath(element, "..")
            if parent_element is None:
                break

            parent_tag = await marchir_util.get_tag_name(parent_element)
            if parent_tag == "html":
                break

            bg_colour = await marchir_util.get_css_property(
                parent_element, "background-color"
            )
            element = parent_element
        except Exception:
            break

    return bg_colour

async def inspect_element_context(element) -> dict:
    """
    Walks up the ancestor chain once and determines:
    - whether the element and ancestors are visible
    - the effective background colour
    - whether any relevant ancestor has a background image
    """
    current = element
    effective_bg = None
    has_bg_image = False

    while current is not None:
        styles = await marchir_util.get_computed_styles(current)
        if not styles:
            return {
                "visible": False,
                "backgroundColor": None,
                "hasBackgroundImage": False,
            }

        display = styles.get("display")
        visibility = styles.get("visibility")
        opacity = styles.get("opacity")
        bg_colour = styles.get("backgroundColor")
        bg_image = styles.get("backgroundImage")

        if display == "none" or visibility == "hidden" or opacity == "0":
            return {
                "visible": False,
                "backgroundColor": None,
                "hasBackgroundImage": False,
            }

        if bg_image and bg_image != "none":
            has_bg_image = True

        if effective_bg is None and bg_colour:
            try:
                if not has_invisible_background(bg_colour):
                    effective_bg = bg_colour
            except Exception:
                pass

        tag_name = await marchir_util.get_tag_name(current)
        if tag_name == "html":
            break

        current = await marchir_util.get_element_with_xpath(current, "..")

    return {
        "visible": True,
        "backgroundColor": effective_bg,
        "hasBackgroundImage": has_bg_image,
    }

async def run_marker(page, marker_results):
    colour_contrast_error_count = 0
    contrast_ratios: list[str] = []

    body_element = await marchir_util.get_element_with_tag_name(page, "body")
    if body_element is None:
        return {
            "ColourContrastErrorCount": 0,
            "ColourContrastRatios": "",
        }

    all_elements = await marchir_util.get_elements_with_xpath(body_element, "//*")

    text_elements: list[tuple[object, str, dict]] = []

    for element in all_elements:
        text = await get_true_text(element)
        if not text:
            continue

        context = await inspect_element_context(element)
        if not context["visible"]:
            continue

        text_elements.append((element, text, context))

    for element, _text, context in text_elements:
        styles = await marchir_util.get_computed_styles(element)
        if not styles:
            continue

        position = styles.get("position")
        text_colour = styles.get("color")
        font_size = styles.get("fontSize")
        font_weight = styles.get("fontWeight")

        if position == "absolute":
            continue

        if not text_colour:
            continue

        if context["hasBackgroundImage"]:
            continue

        bg_colour = context["backgroundColor"]
        if not bg_colour:
            continue

        try:
            if has_transparency(text_colour):
                continue

            if has_transparency(bg_colour) and not has_invisible_background(bg_colour):
                continue

            if has_invisible_background(bg_colour):
                continue
        except ValueError:
            continue

        try:
            text_colour_rgb = rgba_to_rgb_string(text_colour)
            bg_colour_rgb = rgba_to_rgb_string(bg_colour)
        except ValueError:
            continue

        req_ratio = 4.5

        try:
            font_size_px = float(font_size.replace("px", "").strip()) if font_size else 0.0
            tag_name = await marchir_util.get_tag_name(element)
            is_bold = font_weight in ("bold", "700", "800", "900") or tag_name == "b"

            if font_size_px >= 24 or (font_size_px >= 18.5 and is_bold):
                req_ratio = 3.0

        except ValueError:
            pass

        contrast = get_contrast_ratio(text_colour_rgb, bg_colour_rgb)

        if contrast < req_ratio:
            colour_contrast_error_count += 1
            contrast_ratios.append(str(contrast))

    return {
        "ColourContrastErrorCount": colour_contrast_error_count,
        "ColourContrastRatios": ",".join(contrast_ratios),
    }