import pandas as pd

from config.core import engine

class ValidationMessages():

    def __init__(self):
        self.data_frame = pd.read_sql('validation_message', con=engine)

    def find_message_by_code(self, code):
        record = self.data_frame.loc[self.data_frame['code'] == code, 'message']

        if not record.empty:
            return record.values[0]
        else:
            return "ERROR"