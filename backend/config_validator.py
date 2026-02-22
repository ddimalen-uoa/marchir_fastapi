import v1.uploaded.project_validators as project_validators
from v1.uploaded.project_validators import *

validator_functions = {
    'form_validator': project_validators.form_validator.run_validator,
    'selector_validator': project_validators.selector_validator.run_validator    
}

form_id = "form-ct"

form_sections = { 
    "user-details":4, 
    "address-details":2, 
    "contact-details":2
}