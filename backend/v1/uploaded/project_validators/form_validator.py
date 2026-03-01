import v1.uploaded.modules.marchir as marchir_util
import config_validator as config

async def run_validator(page, validation_messages_dataframe):

    print('Form validation starting')

    validation_results = {}

    form_element = await marchir_util.find_form_element(page, config.form_id)

    found_form_element = form_element is not None

    if not found_form_element:
        marchir_util.add_form_status_messages(False, "FORMMISSING", config.form_id, validation_results, validation_messages_dataframe)
        return validation_results
    
    marchir_util.add_form_status_messages(True, "FORMFOUND", config.form_id, validation_results, validation_messages_dataframe)

    for section_id in config.form_sections.keys():
        xpath = "//div[@id=\'{form_id}\']//form//div[contains(@id, \'{section_id}\')]".format(form_id=config.form_id, section_id=section_id)
        section_element = await marchir_util.find_element_by_xpath(page, xpath)

        print("here at 24", section_element)

        if not section_element:
            print("27th")
            marchir_util.add_section_status_messages(False, "SECTIONMISSING", section_id, config.form_id, validation_results, validation_messages_dataframe)
            continue

        marchir_util.add_section_status_messages(True, "SECTIONFOUND", section_id, config.form_id, validation_results, validation_messages_dataframe )

        xpath2 = (
            f'//div[@id="{config.form_id}"]'
            f'//form'
            f'//div[contains(@id, "{section_id}")]'
            f'//input'
        )

        num_fields = int(await marchir_util.element_count_from_xpath(page, xpath2))
        correct_num_of_fields = int(config.form_sections[section_id])

        marchir_util.add_field_number_messages(section_id, num_fields, correct_num_of_fields, validation_results, validation_messages_dataframe)
 
    return validation_results