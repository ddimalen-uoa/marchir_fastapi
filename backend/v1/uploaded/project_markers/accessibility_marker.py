import v1.uploaded.modules.marchir as marchir_util
import config_validator as config

async def checkAltText(page):
    alt_text_word_limit = 2
    penalty = False
    flags = []
    alt_text_dict = {}

    images = page.locator("img")
    count = await images.count()

    for i in range(count):
        image = images.nth(i)
        alt_attr = await image.get_attribute("alt")
        src_attr = await image.get_attribute("src")

        if alt_attr is not None and alt_attr.strip():
            alt_text = alt_attr.strip().replace('"', "'")
            source = src_attr
            word_count = len(alt_text.split())

            if alt_text in alt_text_dict:
                if alt_text_dict[alt_text][0] != source:
                    flags.append(f"Duplicate alt text found: '{alt_text}'")
            else:
                alt_text_dict[alt_text] = (source, word_count)
        else:
            penalty = True

    return (penalty, ";".join(flags), alt_text_dict)


async def checkAnchorTags(page):
    penalty_count = 0

    anchor_tags = page.locator("a")
    count = await anchor_tags.count()

    for i in range(count):
        tag = anchor_tags.nth(i)

        inner_html = await tag.inner_html()
        if not inner_html:
            continue  # Ignore anchor tags that are not visible

        link_text = await tag.inner_text()

        # Check if the link text is empty
        if not link_text or link_text.strip() == "":
            images = tag.locator("img")
            img_count = await images.count()

            for j in range(img_count):
                image = images.nth(j)
                alt_attr = await image.get_attribute("alt")

                if not alt_attr or alt_attr.strip() == "":
                    penalty_count += 1
                    return True

        else:
            # Valid link text
            pass

    return False

async def checkTitleElement(page):
    # Find head element
    head = page.locator("head")
    title = page.locator("title")

    head_count = await head.count()
    title_count = await title.count()

    if head_count == 0 or title_count == 0:
        return True

    # Check that title is inside head
    title_in_head = head.locator("title")
    title_in_head_count = await title_in_head.count()

    if title_in_head_count == 0:
        return True

    title_text = await title.first.text_content()

    if title_text is None or title_text.strip() == "":
        return True

    return False

async def checkDuplicateIds(page):
    penalty_count = 0

    elements = page.locator("[id]")
    count = await elements.count()

    ids = set()  # faster than list for lookups

    for i in range(count):
        element = elements.nth(i)
        element_id = await element.get_attribute("id")

        if not element_id or element_id.strip() == "":
            continue  # Same behaviour as HTMLCS

        if element_id in ids:
            penalty_count += 1
            return True
        else:
            ids.add(element_id)

    return False

async def AriaLabelledbyIsCorrect(page, aria_labelledby):
    label_ids = aria_labelledby.split()

    for label_id in label_ids:
        exists = await page.evaluate(
            "(id) => document.getElementById(id) !== null",
            label_id
        )
        if not exists:
            return False

    return True


async def isLabelWithInputId(page, input_id):
    all_labels = page.locator("label")
    count = await all_labels.count()

    for i in range(count):
        label = all_labels.nth(i)
        label_for = await label.get_attribute("for")
        if label_for == input_id:
            return True

    return False


async def isElementWithinLabel(page, element):
    all_labels = page.locator("label")
    label_count = await all_labels.count()

    for i in range(label_count):
        label = all_labels.nth(i)

        # Check whether the element is inside this label
        is_within = await element.evaluate(
            """(el, labelEl) => labelEl.contains(el)""",
            await label.element_handle()
        )
        if is_within:
            return True

    return False


async def buttonHasText(element, flags):
    try:
        button_text = await element.inner_text()
        inner_html = await element.inner_html()

        # Return True if text is non-empty
        if button_text and button_text.strip():
            return True
        elif inner_html:
            inner_html = inner_html.replace('"', "'")  # Store safely for JSON later
            flags.append(f"Button content not recognised as text: {inner_html}")
            return True
    except Exception:
        return False

    return False


async def buttonHasValue(element):
    try:
        value_attribute = await element.get_attribute("value")
        if value_attribute and value_attribute.strip():
            return True
    except Exception:
        return False

    return False


async def checkProgrammaticallyDeterminedNames(page):
    penalty = False
    flags = []

    select_elements = page.locator("select")
    textarea_elements = page.locator("textarea")
    input_elements = page.locator("input")
    button_elements = page.locator("button")

    select_count = await select_elements.count()
    textarea_count = await textarea_elements.count()
    input_count = await input_elements.count()
    button_count = await button_elements.count()

    elements_to_check = []

    for i in range(select_count):
        elements_to_check.append(select_elements.nth(i))

    for i in range(textarea_count):
        elements_to_check.append(textarea_elements.nth(i))

    for i in range(input_count):
        elements_to_check.append(input_elements.nth(i))

    for i in range(button_count):
        elements_to_check.append(button_elements.nth(i))

    for element in elements_to_check:
        aria_label = await element.get_attribute("aria-label")
        aria_labelledby = await element.get_attribute("aria-labelledby")
        aria_describedby = await element.get_attribute("aria-describedby")
        title = await element.get_attribute("title")
        input_type = await element.get_attribute("type")
        id_attribute = await element.get_attribute("id")
        tag_name = await element.evaluate("(el) => el.tagName.toLowerCase()")

        # Check for input types that don't require label
        if input_type == "hidden":
            continue

        # Buttons
        if input_type == "button" or tag_name == "button":
            if await buttonHasText(element, flags):
                continue

        # Submit/reset buttons
        if input_type in ["submit", "reset"]:
            if await buttonHasValue(element):
                continue
            else:
                penalty = True

        # Image input must have alt text
        if input_type == "image":
            alt_attr = await element.get_attribute("alt")
            if alt_attr and alt_attr.strip():
                continue
            else:
                penalty = True

        # Explicit label using for/id
        if id_attribute:
            if await isLabelWithInputId(page, id_attribute):
                continue

        # Implicit label
        if await isElementWithinLabel(page, element):
            continue

        # aria-labelledby points to existing ids
        if aria_labelledby:
            if await AriaLabelledbyIsCorrect(page, aria_labelledby):
                continue

        # aria-label / aria-describedby / title fallback
        if not any([aria_label, aria_describedby, title]):
            penalty = True

    flags = ";".join(flags)
    return penalty, flags

async def run_marker(page, marker_results):
    accessibility_error = 0
    accessibility_error_list = []
    flags = []

    # altTextMarker
    alt_text_penalty, alt_text_flags, alt_text_dict = await checkAltText(page)
    if alt_text_penalty:
        accessibility_error += 1
        accessibility_error_list.append("WCAG2AA.Principle1.Guideline1_1.1_1_1.H37")    
    flags.append(alt_text_flags)
    alt_text_list = [alt_text for alt_text in alt_text_dict.keys()][:5] # Limit to first five
    alt_text_word_counts = [str(alt_text[1]) for alt_text in alt_text_dict.values()]

    # hrefMarker
    checkAnchorTagsResult = await checkAnchorTags(page)
    if checkAnchorTagsResult:
        accessibility_error += 1
        accessibility_error_list.append("WCAG2AA.Principle1.Guideline1_1.1_1_1.H30.2")    

    # titleMarker
    # title_results = checkTitleElement(driver)
    checkTitleElementResult = await checkTitleElement(page)
    if checkTitleElementResult:
        accessibility_error += 1
        accessibility_error_list.append("WCAG2AA.Principle2.Guideline2_4.2_4_2.H25.1.NoTitleEl")

    # id_results = checkDuplicateIds(page)
    checkDuplicateIdsResult = await checkDuplicateIds(page)
    if checkDuplicateIdsResult:
        accessibility_error += 1
        accessibility_error_list.append("WCAG2AA.Principle4.Guideline4_1.4_1_1.F77")

    # ui_name_results = checkProgrammaticallyDeterminedNames(driver)
    F68_penalty, F68_flags = await checkProgrammaticallyDeterminedNames(page)
    if F68_penalty:
        accessibility_error += 1
        accessibility_error_list.append("WCAG2AA.Principle1.Guideline1_3.1_3_1.F68")
    flags.append(F68_flags)

    accessibility_errors_string = "".join(accessibility_error_list)
    flags_string = ";".join(flags)
    alt_text_string = ";".join(alt_text_list)
    alt_word_count_string = ",".join(alt_text_word_counts)    

    return {
        'Accessibility Error Count': accessibility_error,
        'Accessibility Errors': accessibility_errors_string,
        'Accessibility Flags': flags_string,
        'Alt Text Found': alt_text_string,
        'Alt Text Word Counts': alt_word_count_string
    } 