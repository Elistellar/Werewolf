import json
from pathlib import Path


class Settings:
    
    @classmethod
    def load(cls):
        with open('settings.json', encoding='utf-8') as file:
            cls.data = json.load(file)
            
    def __class_getitem__(cls, key):
        return cls.data[key]
