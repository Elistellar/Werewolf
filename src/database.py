import sqlite3
from typing import Any
import logging as log


def lock():
    def decorator(func):
        def wrapper(cls, *args, **kwargs):
            while cls._locked:
                pass
            
            cls._locked = True
            r = func(cls, *args, **kwargs)
            cls._locked = False
            
            return r
            
        return wrapper
    return decorator

class Database:
    
    types = {
        int: 'INT',
        bool: 'BOOLEAN',
    }
    
    tables = {
        'games': {
            'owner_id': int,
            'guild_id': int,
            'owner_id': int,
            'category_id': int,
            'settings_channel_id': int,
            'voice_channel_id': int,
            'werewolves_channel_id': int,
            'settings_panel_id': int,
                        
            'werewolves_number': int,
            'villagers_number': int,
            'little_girl': bool,
            'hunter': bool,
            'cupid': bool,
            'thief': bool,
            
            'sheriff_user_id': bool,
            'night_number': bool,
            'night_state': bool,
            'heal_potion': bool,
            'death_potion': bool,
        },
        'players': {
            'user_id': int,
            'game_id': int,
            'role_id': int,
            'is_alive': bool,
            'is_ready': bool,
        },
        'stats': {
            'user_id': int,
            'game_played': int,
            'game_won': int,
        }
    }
    
    @classmethod
    def load(cls):
        cls.con = sqlite3.connect('database.db')
        cls.cur = cls.con.cursor()
        cls._locked = False
        
        # create tables if not exists
        for name, data in cls.tables.items():
            cls.cur.execute(f'CREATE TABLE IF NOT EXISTS {name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {", ".join([f"{key} {cls.types[val]}" for key, val in data.items()])})')
            data.update({'id': int})

        cls.con.commit()

    @classmethod
    def insert(cls, table: str, values: dict[str, Any]):
        
        sql = f'INSERT INTO {table} ({", ".join(values.keys())}) VALUES ({", ".join([str(val) for val in values.values()])})'.replace('None', 'NULL')
        log.sql(sql)
        
        cls.cur.execute(sql)
        cls.con.commit()
        
    @classmethod
    def select(cls, table: str, vars: list[str] = ['*'], where: str = None, order: str = None) -> list[dict[str, Any]]:
        sql = f'SELECT {", ".join(vars)} FROM {table}{" WHERE " + where if where else ""}{" ORDER BY " + order if order else ""}'
        log.sql(sql)
        cls.cur.execute(sql)
        
        if vars == ['*']:
            vars = list(cls.tables[table].keys())

        r = [
            {
                var: cls.tables[table][var](val) if val != 'NULL' else None
                for var, val in zip(vars, row)
            }
            for row in cls.cur.fetchall()
        ]
        
        lenr = len(r)
        log.sql(f'-> {lenr} result{"s" if lenr > 1 else ""}' + str(":\n                 - " if lenr > 0 else "") + '\n                 - '.join([str(row) for row in r]))
        return r

    @classmethod
    def delete(cls, table: str, where: str = None):
        sql = f'DELETE FROM {table}{" WHERE " + where if where else ""}'
        log.sql(sql)
        cls.cur.execute(sql)
        cls.con.commit()

    @classmethod
    def update(cls, table: str, values: dict[str, Any], where: str):
        sql = f'UPDATE {table} SET {", ".join([var + "=" + str(val) for var, val in values.items()])}{" WHERE " + where if where else ""}'
        log.sql(sql)
        cls.cur.execute(sql)
        cls.con.commit()
