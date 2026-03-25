from typing import Optional
from playwright.async_api import async_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError
import config_marker as config
import json

async def find_form_element(page: Page, form_id: str = "form-ct") -> Optional[Locator]:
    xpath = f'//div[@id="{form_id}"]//form'
    locator = page.locator(f"xpath={xpath}")

    # "exists" check: count() hits the DOM and returns 0 if not found
    if await locator.count() == 0:
        return None

    # If you specifically want the first matching form
    return locator.first

async def find_element_by_xpath(page: Page, xpath: str):
    locator = page.locator(f"xpath={xpath}")

    # "exists" check: count() hits the DOM and returns 0 if not found
    if await locator.count() == 0:
        return None

    # If you specifically want the first matching form
    return locator.first

async def get_element_with_tag_name(page, tag_name):
    locator = page.locator(tag_name)

    if await locator.count() == 0:
        return None

    return locator.first

async def element_count_from_xpath(page: Page, xpath: str):
    locator = page.locator(f"xpath={xpath}")

    count = await locator.count()

    return count

def add_form_status_messages(is_form_found, message_code, form_id, validation_results, validation_messages_dataframe):
    '''
    A function adds the formatted result message for the form status to the final result dictionary.

    Parameters:
        is_form_found (str): True(if the form exists), False(if the form does not exist)
        message_code (str): a message code to look up the corresponding message in the validation_messages_dataframe
        form_id (str): the id attribute for the form 
        validation_results (dic): a dictionary where the key is a criterion title and the value is a list [result in boolean, result message]. The validation result for the form will be added.
        validation_messages_dataframe: an sql table used to look up a validation message corresponding to a validation code. 
    '''
    validation_result_message_unformatted = validation_messages_dataframe.find_message_by_code(message_code)
    validation_result_message = validation_result_message_unformatted.format(form_id=form_id)
    validation_results['{form_id} form'.format(form_id=form_id)] = [is_form_found, validation_result_message]

def add_section_status_messages(is_section_found, message_code, section_id, form_id, validation_results, validation_messages_dataframe):
    '''
    A function adds the formatted result message for the section status to the final result dictionary.

    Parameters:
        is_section_found (bool): True (if the section exists), False (the section does not exist)
        message_code (str): a message code to look up the corresponding message in the validation_messages_dataframe
        section_id (str): the name of section that is being checked
        form_id (str): the id attribute for the form 
        validation_results (dic): a dictionary where the key is a criterion title and the value is a list [result in boolean, result messsage]. The validadtion result for the section will be added.
        validtion_messaes_dataframe: an sql table used to look up a validation message corresponding to a validation code. 
    '''
    validation_result_messages_unformatted_sections = validation_messages_dataframe.find_message_by_code(message_code)
    validation_result_message = validation_result_messages_unformatted_sections.format(section_id=section_id, form_id=form_id)
    validation_results['{section_id} section'.format(section_id=section_id)] = [is_section_found, validation_result_message]

def add_field_number_messages(section_id, num_fields, correct_num_of_fields, validation_results, validation_messages_dataframe ):
    '''
    A function determines if a section has the correct number of input elements, and adds the formatted result message to the final result dictinary.

    Parameters:
        section_id (str): the name of section that is being checked
        num_fields (int): the number of input elements in the section
        correct_num_of_fields (int): the correct number of input elements in the section
        validation_results (dic): a dictionary where the key is a criterion title and the value is a list [result in boolean, result messsage]. The validation result for the input number will be added.
        validation_messages_dataframe: an sql table used to look up a validation message corresponding to a validation code. 
    '''
    if num_fields == correct_num_of_fields:
        message_code = "SECTIONCORRECTFIELDS"
        validation_result_boolean_fields = True
    elif num_fields > correct_num_of_fields:
        message_code = "SECTIONTOOMANYFIELDS"
        validation_result_boolean_fields = False
    elif num_fields < correct_num_of_fields:
        message_code = "SECTIONNOTENOUGHFIELDS"
        validation_result_boolean_fields = False

    validation_result_messages_unformatted_fields = validation_messages_dataframe.find_message_by_code(message_code)
    validation_result_message = validation_result_messages_unformatted_fields.format(section_id=section_id, num_fields=correct_num_of_fields)
    validation_results['{section_id} section fields'.format(section_id=section_id)] = [validation_result_boolean_fields, validation_result_message]


async def execute_marker(page: Page):

    # Take a screenshot of the page
    await page.screenshot(path="/uploads/test.png", full_page=True)

    marker_results = {}

    for marker_name in config.marker_functions.keys():
        marker_function_results = await config.marker_functions[marker_name](page, marker_results)

        for marker_title in marker_function_results.keys():
            marker_result = marker_function_results[marker_title]
            marker_results[marker_title] = marker_result

    return "Done Screenshot"

async def is_displayed(element) -> bool:
    try:
        return await element.is_visible()
    except Exception:
        return False
    
async def get_element_with_xpath(scope, xpath: str):
    try:
        locator = scope.locator(f"xpath={xpath}").first
        count = await locator.count()
        return locator if count > 0 else None
    except Exception:
        return None
    
async def get_elements_with_xpath(scope, xpath: str):
    try:
        locator = scope.locator(f"xpath={xpath}")
        count = await locator.count()
        print("get_elements_with_xpath count", count)
        return [locator.nth(i) for i in range(count)]
    except Exception:
        return []
    
async def get_text(element):
    try:
        text = await element.inner_text()
        stripped = text.strip()
        return stripped if stripped else None
    except Exception:
        return None
    
async def get_attribute(element, attribute: str):
    try:
        return await element.get_attribute(attribute)
    except Exception:
        return None
    
async def get_tag_name(element):
    try:
        return await element.evaluate("(el) => el.tagName.toLowerCase()")
    except Exception:
        return None
    
async def wait_for_clickable_element_with_id(page, element_id: str, timeout: int = 10000):
    locator = page.locator(f"#{element_id}").first
    await locator.wait_for(state="visible", timeout=timeout)
    return locator
    
async def wait_for_visible_element_with_id(page, element_id: str, timeout: int = 10000):
    locator = page.locator(f"#{element_id}").first
    await locator.wait_for(state="visible", timeout=timeout)
    return locator

async def click_element(element):
    return await element.click()

async def get_css_property(element, css_property: str):
    try:
        return await element.evaluate(
            "(el, prop) => window.getComputedStyle(el).getPropertyValue(prop)",
            css_property,
        )
    except Exception:
        return None
    
async def get_element_with_css_selector(scope, selector: str):
    try:
        locator = scope.locator(selector).first
        count = await locator.count()
        return locator if count > 0 else None
    except Exception:
        return None


async def get_elements_with_css_selector(scope, selector: str):
    try:
        locator = scope.locator(selector)
        count = await locator.count()
        return [locator.nth(i) for i in range(count)]
    except Exception:
        return []

async def get_computed_styles(element):
    try:
        return await element.evaluate("""
            (el) => {
                const s = window.getComputedStyle(el);
                return {
                    color: s.getPropertyValue("color"),
                    backgroundColor: s.getPropertyValue("background-color"),
                    backgroundImage: s.getPropertyValue("background-image"),
                    fontSize: s.getPropertyValue("font-size"),
                    fontWeight: s.getPropertyValue("font-weight"),
                    position: s.getPropertyValue("position"),
                    display: s.getPropertyValue("display"),
                    visibility: s.getPropertyValue("visibility"),
                    opacity: s.getPropertyValue("opacity"),
                };
            }
        """)
    except Exception:
        return None