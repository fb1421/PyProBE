import polars as pl
import re
class Units:
    unit_dict = {
        'Current': {
            'units': ['A', 'mA'],
            'scale_factor': [1, 1000],
            'zero_reference': False
        },
        'Voltage': {
            'units': ['V', 'mV'],
            'scale_factor': [1, 1000],
            'zero_reference': False
        },
        'Capacity': {
            'units': ['Ah', 'mAh'],
            'scale_factor': [1, 1000],
            'zero_reference': True
        },
        'Time': {
            'units': ['s', 'min', 'hr'],
            'scale_factor': [1, 1/60, 1/3600],
            'zero_reference': True
        },
    }

    @staticmethod
    def extract_quantity_and_unit(string):
        match = re.search(r'\[(.*?)\]', string)
        if match:
            unit = match.group(1)
            quantity = string.replace(f'[{unit}]', '').strip()
        else:
            quantity = string
            unit = None
        return quantity, unit
    
    @classmethod
    def convert_units(cls, column):
        quantity, unit_from =cls.extract_quantity_and_unit(column)
        if quantity in cls.unit_dict.keys():
            polars_instruction_list = []
            for unit_to in cls.unit_dict[quantity]['units']:
                if unit_to != unit_from:
                    scale_factor = cls.unit_dict[quantity]['scale_factor'][cls.unit_dict[quantity]['units'].index(unit_to)]
                    polars_instruction_list.append((pl.col(column) * scale_factor).alias(f'{quantity} ({unit_to})'))
            return polars_instruction_list
        
    @classmethod
    def set_zero(cls, column):
        quantity, _ = cls.extract_quantity_and_unit(column)
        if quantity in cls.unit_dict.keys():
            if cls.unit_dict[quantity]['zero_reference']==True:
                return [pl.col(column) - pl.col(column).first()]