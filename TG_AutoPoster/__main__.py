import sys
from .TG_AutoPoster import create_parser, log, AutoPoster


if __name__ == "__main__":
    args = create_parser().parse_args()
    if args.debug:
        log.add(sys.stdout, colorize=True)
        log.add("./logs/bot_log_DEBUG.log", level="DEBUG", rotation="5 MB")
    log.info("Начало работы.")
    autoposter = AutoPoster(config_path=args.config, cache_dir=args.cache_dir, ipv6=args.ipv6)
    if args.loop or args.sleep:
        sleep_time = args.sleep if args.sleep else 3600
        log.info("Программе был передан аргумен --loop (-l). Запуск бота в бесконечном цикле.")
        autoposter.infinity_run(interval=sleep_time)
    else:
        autoposter.run()
    log.info("Работа завершена. Выход.")
