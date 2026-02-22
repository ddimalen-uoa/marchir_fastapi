from typing import Optional
from playwright.async_api import async_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError

async def find_form_element(page: Page, form_id: str = "form-ct") -> Optional[Locator]:
    xpath = f'//div[@id="{form_id}"]//form'
    locator = page.locator(f"xpath={xpath}")

    # "exists" check: count() hits the DOM and returns 0 if not found
    if await locator.count() == 0:
        return None

    # If you specifically want the first matching form
    return locator.first

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
