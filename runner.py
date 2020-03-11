# -*-*- coding: utf-8 -*-*-

from config import Config, conf_logging
from webapp import app

if Config.DEBUG:
    import traceback


def main():
    app.run(host=Config.API_HOST, port=Config.API_PORT)


if __name__ == '__main__':
    conf_logging(Config.APPNAME, syslog=True)
    main()
