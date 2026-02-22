import v1.uploaded.modules.marchir as marchir_util
import config_validator as config

async def run_validator(page, validation_messages_dataframe):

    print('Form validation starting')
    print(validation_messages_dataframe)

    validation_results = {}

    form_element = await marchir_util.find_form_element(page, config.form_id)

    found_form_element = form_element is not None

    if not found_form_element:
        marchir_util.add_form_status_messages(False, "FORMMISSING", config.form_id, validation_results, validation_messages_dataframe)
        return validation_results
    
    marchir_util.add_form_status_messages(True, "FORMFOUND", config.form_id, validation_results, validation_messages_dataframe)

    

    return validation_results


async def run_validator_orig(page): 

    print('Form validation starting')

    el = await page.query_selector("#test")
    found = el is not None

    form_element = marchir_util.find_form_element(page, config.form_id)

    found_form_element = form_element is not None

    if found_form_element:
        print(f"Found nyahahaha {config.form_id}")
    else:
        print(f"Not Found {config.form_id}")    

    if found:
        print("Helllsdkfsdlfkjsdfklj")

    return f"Hellow there!!!! from form_validator"