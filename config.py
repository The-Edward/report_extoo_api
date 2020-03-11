# -*-*- coding: utf-8 -*-*-

import os
from envparse import env
from flask import request
import logging
import logging.handlers


class Config:
    DISABLE_AUTH = False
    SECRET_KEY = os.urandom(16)

    # Файл с переменными ".env"
    env.read_envfile()
    LOG_LEVEL = env.str('LOG_LEVEL', default='INFO')
    DEBUG = False
    if LOG_LEVEL == 'DEBUG':
        DEBUG = True

    REST_TIME = env.int('REST_TIME', default=4)

    APPNAME = env.str('APPNAME', default='default application')
    OLD_DAYS_LOGINS = env.int('OLD_LOGINS', default=17)
    PREFIX_OO = env.list('PREFIX_OO', default=[])

    # options for flask
    LOGGER_NAME = APPNAME
    API_HOST = env.str('API_HOST', default='localhost')
    API_PORT = env.int('API_PORT', default=5050)
    CSRF_ENABLED = True
    DISABLE_REAL_NAMES = env.bool('DISABLE_REAL_NAMES', default=False)

    # options for base
    DB_HOST = env.str('DB_HOST', default='localhost')
    DB_PORT = env.int('DB_PORT', default=5432)
    DB_BASE = env.str('DB_BASE', default='postgres')
    DB_USER = env.str('DB_USER', default='postgres')
    DB_PASS = env.str('DB_PASS', default='')

    # options for LDAP
    LD_SERVER = env.str('LD_SERVER', default='ldap://localhost:389')
    LD_USER = env.str('LD_USER', default='')
    LD_PASS = env.str('LD_PASS', default='')
    LD_BASE_DN = env.str('LD_BASE_DN', default='')
    LD_PAGE_SIZE = env.int('LD_PAGE_SIZE', default=1000)


def conf_logging(name: str = None, syslog: bool = False, level: str = 'INFO'):
    """
    Настройка логирования.
    Лог всегда выводится в стандартный вывод

    Для работы с логером использовать рекомендуемый способ logging.getLogger.

    :param name: имя приложения
    :param syslog: выводить дополнительно в syslog
    :param level: инициализация уровня логирования
    :return:
    """
    _name = name
    if not _name:
        _name = __name__
    _level = level
    if level:
        _level = getattr(logging, level)
    if Config.DEBUG:
        _level = logging.DEBUG
    log = logging.getLogger(_name)
    log.setLevel(_level)
    formatter = logging.Formatter('%(asctime)s: %(name)s: %(module)s: %(levelname)s: %(message)s')
    # formatter = logging.Formatter('%(asctime)s: %(name)s: %(levelname)s: %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    log.addHandler(handler)
    if syslog:
        hsyslog = logging.handlers.SysLogHandler(address='/dev/log')
        formatter = logging.Formatter('%(name)s: %(module)s: %(levelname)s: %(message)s')
        # formatter = logging.Formatter('%(name)s: %(levelname)s: %(message)s')
        hsyslog.setFormatter(formatter)
        log.addHandler(hsyslog)


def cip():
    return request.remote_addr
