# from datetime import datetime
import logging as log
# from pathlib import Path

# add sql level
SQL_LEVEL_NUM = 15
log.addLevelName(SQL_LEVEL_NUM, 'SQL')
def sql(self, message, *args, **kws):
    if self.isEnabledFor(SQL_LEVEL_NUM):
        # Yes, logger takes its '*args' as 'args'.
        self._log(SQL_LEVEL_NUM, message, args, **kws) 

log.Logger.sql = sql

# generate filename and dirs
# log_filename = datetime.now().strftime('%Y-%m-%d %Hh%M.log')
# log_filepath = Path(__file__).resolve().parent / 'logs' / log_filename

# if not log_filepath.parent.exists():
#     log_filepath.parent.mkdir()

# init logger
log.basicConfig(
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

logger = log.getLogger('werewolf')
logger.setLevel(SQL_LEVEL_NUM)
# logger.addHandler(log.FileHandler(log_filepath))
# logger.addHandler(log.StreamHandler())
# TODO: add discord handler
log.sql = logger.sql
log.info = logger.info

# run bot
from src.bot import bot
from src.settings import Settings

bot.run(Settings['token'])