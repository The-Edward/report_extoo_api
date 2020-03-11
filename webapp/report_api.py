# -*-*- coding: utf-8 -*-*-

import json
import time
from functools import wraps
from logging import getLogger

import pam
import time
from flask import Response, stream_with_context, request, session

from config import Config, cip
from webapp import app
from .waiters import get_oo_info, get_oo_info_all_2


def login_required(f):
    log = getLogger(Config.APPNAME)
    if Config.DISABLE_AUTH:
        log.warning('DISABLE_AUTH is %s!' % Config.DISABLE_AUTH)
        return f

    @wraps(f)
    def wrapped_view(**kwargs):
        auth = request.authorization
        pau = pam.pam()
        user = ''
        # reason = 'Unauthorized'
        reason = {'error': 'Unauthorized'}
        if not (auth and pau.authenticate(auth.username, auth.password)):
            if pau.reason:
                reason['error'] = pau.reason
            if (auth and auth.username):
                user = '"%s"' % auth.username
            log.warning(f'''{cip()}: User {user} not auth: {reason['error']}''')
            return (reason, 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'
            })

        return f(**kwargs)

    return wrapped_view


def requests_more_slowly(f):
    """Ограничивает частоту запросов к защищаемому ресурсу

    Также реализована защита от множественных запросов в рамках одной сессии.
    В защищаемой функции в начале добавить "session['active'] = True", а в конце
    добавить "session['active'] = False" для указания признака окончания запроса
    """
    log = getLogger(Config.APPNAME)

    @wraps(f)
    def wrapped_view(**kwargs):
        user = ''
        auth = request.authorization

        if 'active' not in session:
            session['active'] = False

        if 'time' not in session:
            session['time'] = time.time()
            return f(**kwargs)
        last_time = session['time']

        if (auth and auth.username):
            user = '"%s"' % auth.username

        reason = {'error': f'''Too Many Requests  (Allow retry at {Config.REST_TIME}s)'''}
        if (time.time() - last_time) < float(Config.REST_TIME) or session['active']:
            log.warning(f'''{cip()}: User {user} not allowed: {reason['error']}''')
            return (reason, 429, {
                'Retry-After': '%s seconds' % Config.REST_TIME
            })
        else:
            session['time'] = time.time()
            # session['active'] = True

        return f(**kwargs)

    return wrapped_view


@app.route('/extooall/')
@login_required
@requests_more_slowly
def show_extoo_all():
    """Вывод в формате JSON данных по всем логинам """
    log = getLogger(Config.APPNAME)
    session['active'] = True

    def gout():
        log.info(f'''{cip()}: Start generate JSON external IP''')
        flag_begin_json = True
        dt = time.time()
        yield '['
        for rec in get_oo_info_all_2(Config.PREFIX_OO):
            for val in rec:
                if flag_begin_json:
                    flag_begin_json = False
                else:
                    yield ','
                yield json.dumps(val, ensure_ascii=False)
        yield ']'
        session['active'] = False
        log.info(f'''{cip()}: Done generate JSON external IP''')
        log.info(f'''{cip()}: Time spent: {time.time()-dt}''')

    return Response(stream_with_context(gout()), mimetype='application/json')


@app.route('/')
def index1(file: str=None):
    # def oo(file=None):
    #     if not file:
    #         yield ''
    #     with open(file, 'rb') as hh:
    #         yield hh.read()
    tdata = f'''<html>
    <title>{Config.APPNAME}</title>
    <a href="/extoo/">/extoo/<логин></a><br>
    <a href="/extooall/">/extooall/</a>
    </html>'''
    # return Response(stream_with_context(oo(file)), mimetype='application/octet')
    return tdata


@app.route('/extoo/')
@app.route('/extoo/<login>')
@login_required
@requests_more_slowly
def show_extoo(login: str = None):
    """Вывод в формате JSON данных по заданному логину """

    text = 'Не указан логин'
    if not login:
        return {'info': text}
    # защита от ИБ
    login = str(login[:79])
    return {login: get_oo_info(login)}
