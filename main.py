import sys
from os import mkdir, chdir

try:
    mkdir('data')
    chdir('data')
except FileExistsError:
    chdir('data')

from telegram.ext import *
from settings import config
import starter
from botlogs import log


def error(bot, update, error):
    log.warning('[TG] Update "%s" caused error "%s"' % (update, error))


if __name__ == '__main__':
    def job_repeated(bot, job):
        starter.starter(bot)


    def update(request_kwargs=None):
        global updater, dp, job_queue
        updater = Updater(config.get('global', 'bot_token'), request_kwargs=request_kwargs)
        dp = updater.dispatcher
        job_queue = updater.job_queue
        dp.add_handler(CommandHandler('start', starter.start))
        dp.add_handler(CommandHandler('help', starter.help))
        dp.add_handler(MessageHandler(callback=starter.is_admin, filters=Filters.text))
        job = job_queue.run_repeating(job_repeated, interval=5 * 60, first=0)


    if config.get('global', 'proxy_url'):
        REQUEST_KWARGS = {'proxy_url': config.get('global', 'proxy_url')}
        update(REQUEST_KWARGS)
    else:
        update()

    dp.add_error_handler(error)
    # noinspection PyBroadException
    try:
        updater.start_polling()
        updater.idle()
    except Exception:
        log.warning('Critical error occured: {0} {1}. Please restart a bot.'.format(sys.exc_info()[0], sys.exc_info()[1]))
