from fastapi import HTTPException

ACCOUNT_SUSPENDED_MESSAGE = (
    "Your account has been suspended. Please contact "
    "d.dimalen@auckland.ac.nz for more information."
)


class AccountSuspendedError(HTTPException):
    def __init__(self):
        super().__init__(status_code=403, detail=ACCOUNT_SUSPENDED_MESSAGE)
