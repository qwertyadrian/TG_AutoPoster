from pyrogram.types import (InlineQuery, InlineQueryResultArticle,
                            InputTextMessageContent)

from .. import AutoPoster
from ..utils.tg import tools


@AutoPoster.on_inline_query(tools.is_admin)
def inline(bot: AutoPoster, query: InlineQuery):
    string = query.query.lower()

    results = []

    bot.reload_config()
    sources_list = bot.config.get("domains", {}).keys()

    for source in sources_list:
        if not string or source.startswith(string):
            text, reply_markup = tools.generate_setting_info(bot, source)
            results.append(
                InlineQueryResultArticle(
                    title=source,
                    input_message_content=InputTextMessageContent(
                        text, disable_web_page_preview=True
                    ),
                    reply_markup=reply_markup,
                )
            )

    query.answer(results=results, cache_time=0)
