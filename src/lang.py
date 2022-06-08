import json
from typing import Any
from pathlib import Path

from discord.ext.commands import Bot


def plural(var: int) -> str:
    return 's' if var > 1 else ''

class Lang:
    
    @classmethod
    def load(cls, bot: Bot):
        
        cls.emojis = {
            emoji.name + '_emote': str(emoji)
            for emoji in bot.emojis
        }
        
        path =  Path(__file__).resolve().parent.parent / 'lang' / 'fr.json'
        with open(str(path), encoding='utf-8') as f:
            cls.data = json.load(f)
    
    def __class_getitem__(cls, key: str) -> str:
        return cls.data[key]
    
    @classmethod 
    def get(cls, key: str, vars: dict[str, Any]) -> str:
        vars.update(cls.emojis)
        vars.update({'plural': plural})
           
        text = cls.data[key].replace('\n', '@@n')
        return eval(f'f"{text}"', vars).replace('@@n', '\n')
