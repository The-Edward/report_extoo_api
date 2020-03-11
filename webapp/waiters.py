# -*-*- coding: utf-8 -*-*-

from contextlib import closing
from logging import getLogger

import psycopg2 as pg
from ldap3 import Server, Connection, ALL, ALL_ATTRIBUTES, DEREF_NEVER
from psycopg2.extras import RealDictCursor as Dcr

from config import Config, cip

if Config.DEBUG:
    pass


class OmmLDAPError(Exception):
    pass


class OmmPGError(Exception):
    pass


def _select_pg(sql: str, args: dict):
    """Запрос в БД"""

    log = getLogger(Config.APPNAME)
    rout = []
    try:
        with closing(pg.connect(host=Config.DB_HOST, dbname=Config.DB_BASE, user=Config.DB_USER,
                                password=Config.DB_PASS)) as conn:
            with conn.cursor(cursor_factory=Dcr) as cursor:
                cursor.execute(sql, args)
                for rec in cursor:
                    # log.debug(rec)
                    yield rec
    except Exception as e:
        raise OmmPGError('PG', e)


def _prep_pg_out(records):
    """Вывод только нужных столбцов, а не всех"""

    avail = 'Логин Адрес_vpn Внешний_адрес'
    out = []
    for rec in records:
        nline = {}
        for el in rec:
            if el in avail:
                nline[el] = rec[el]
        yield nline


def get_oo_info(login: str, descr: str = None):
    """Получение внешнего и внутреннего адресов для указанного логина    """
    log = getLogger(Config.APPNAME)

    sql = """SELECT username Логин, framedipaddress Адрес_vpn, callingstationid Внешний_адрес, nasidentifier,
    acctstarttime, COALESCE(NULLIF(acctstoptime, NOW()),NOW()) as acctstoptime, acctlastupdate
    FROM public.radacct
    WHERE (acctstoptime IS null OR
            NOW() - acctlastupdate < interval '1 month' )
            AND username = %(login)s
    ORDER BY acctstoptime DESC
    LIMIT 1
"""

    args = {
        'login': login
    }

    real_out = []
    try:
        for el in _prep_pg_out(_select_pg(sql, args)):
            real_out.append(el)

        if not Config.DISABLE_REAL_NAMES:
            if len(real_out) > 0:
                real_out[0]['Название'] = descr
                if not descr:
                    real_out[0]['Название'] = get_login_from_ldap(login)
            else:
                real_out = ['Данных по запрошенному логину не найдено']

    except Exception as e:
        log.error(cip()+': '+str(e))
        real_out = ['Ошибка работы с БД']
    return real_out[0]


def _prep_by_ldap(records, ldall):
    """Добавляет название для записи если она есть в LDAP.

    :param record: запись из PG
    :param ldall: набор даххых из LDAP
    """
    log = getLogger(Config.APPNAME)

    # сделать словарь из ldall: {login: displayName}
    ldict = {}
    for el in ldall:
        if el.get('type') and el['type'] == 'searchResEntry':
            # log.debug(el['dn'])
            if el['attributes'].get('sAMAccountName'):
                ldict[el['attributes'].get('sAMAccountName')] = el['attributes'].get('displayName')

    for val in records:
        for recdb in val:

            if not Config.DISABLE_REAL_NAMES:

                try:
                    recdb['Название'] = ldict[recdb['Логин']]
                except KeyError:
                    recdb['Название'] = ''

            yield recdb


def get_oo_info_all_2(prefixes: list):
    """Возвращает все УЗ с адресами и названием.

    Получает список доступных УЗ из LDAP, генератором проходит по БД PG, если УЗ есть в LDAP,
    то добавляет название и выводит
    :param prefixes: список префиксов (ogm, omd, и так далее)
    """
    log = getLogger(Config.APPNAME)

    for prefix in prefixes:
        log.info(f'''{cip()}: Prefix "{prefix}" in progress''')

        ldall = []
        subfilter = f'''(sAMAccountName={prefix}_*)'''
        ldfilter = '(&(memberOf=CN=OMG_ALL,OU=Groups,OU=Service,DC=corp,DC=ru){omm})'.format(omm=subfilter)
        for el in _select_ld_gen(ldfilter):
            ldall.append(el)
        log.info(f'''{cip()}: LDAP complete for prefix "{prefix}"''')

        yield _prep_by_ldap(get_oo_info_by_pref(prefix), ldall)


def get_oo_info_by_pref(prefix: str):
    """Получение внешних и внутренних адресов для указанного типа
    """
    log = getLogger(Config.APPNAME)
    prefix += '%'

    sql = """SELECT DISTINCT ON(username) username as Логин, framedipaddress as Адрес_vpn, acctstarttime,
    callingstationid as Внешний_адрес, MAX(acctstoptime) as acctstoptime
    FROM public.radacct
    WHERE username like %(prefix)s
    AND NOW() - acctstarttime < interval '%(olddays)s day'
    GROUP BY username, acctstoptime, acctstarttime, framedipaddress, callingstationid
    ORDER BY username, acctstoptime desc NULLS FIRST;
    """
    args = {
        'prefix': prefix,
        'olddays': Config.OLD_DAYS_LOGINS
    }

    real_out = ['Ошибка работы с БД']
    log.info(f'''{cip()}: Prepare info from PG for "{prefix}"''')

    try:
        yield _prep_pg_out(_select_pg(sql, args))
    except Exception as e:
        log.error(cip()+': '+str(e))
        yield real_out

    log.info(f'''{cip()}: Done prepare info from PG for "{prefix}"''')


def get_login_from_ldap(login: str):
    """Возвращает данные из ldap - поле displayName
    """
    log = getLogger(Config.APPNAME)
    out = ''
    try:
        subfilter = '(sAMAccountName={login})'.format(login=login)
        ldfilter = '(&(memberOf=CN=OMG_ALL,OU=Groups,OU=Service,DC=corp,DC=ru){omm})'.format(omm=subfilter)

        for el in _select_ld(ldfilter):
            # el['dn']
            # el['attributes'].get('description')
            # el['type']='searchResEntry'
            # el['attributes'].keys()
            # el['attributes'].get('cn')
            # dict_keys(['objectClass', 'cn', 'description', 'distinguishedName', 'instanceType', 'whenCreated',
            # 'whenChanged', 'displayName', 'uSNCreated', 'memberOf', 'uSNChanged', 'name', 'objectGUID',
            # 'userAccountControl', 'codePage', 'countryCode', 'pwdLastSet', 'primaryGroupID', 'objectSid',
            # 'accountExpires', 'sAMAccountName', 'sAMAccountType', 'userPrincipalName', 'objectCategory',
            # 'dSCorePropagationData', 'lastLogonTimestamp', 'uidNumber', 'gidNumber', 'unixHomeDirectory',
            # 'loginShell', 'radiusReplyItem'])

            if el.get('type') and el['type'] == 'searchResEntry':
                if el['attributes'].get('displayName'):
                    out = el['attributes'].get('displayName')
    except Exception as e:
        log.error(cip()+': '+str(e))
    return out


def _select_ld(filter: str):
    """Производит поиск в ldap
    Используется для поиска конкретного значения
    """
    log = getLogger(Config.APPNAME)
    out = []
    ldconn = _connect_ld()

    try:
        ldconn.search(
            search_base=Config.LD_BASE_DN,
            search_filter=filter,
            dereference_aliases=DEREF_NEVER,
            attributes=ALL_ATTRIBUTES
        )

        out = ldconn.response

    except Exception as e:
        raise OmmLDAPError(e)

    if ldconn:
        ldconn.unbind()
    if Config.DEBUG:
        log.debug(f'''{cip()}: Disconnect from "{ldconn}"''')
    return out


def _select_ld_gen(filter: str):
    """Производит поиск в ldap
    Используется для поиска группы значений.
    Возвращает генератор
    """

    log = getLogger(Config.APPNAME)
    out = []
    ldconn = _connect_ld()

    try:
        with ldconn as conn:
            entry_generator = conn.extend.standard.paged_search(search_base=Config.LD_BASE_DN, search_filter=filter,
                                                                dereference_aliases=DEREF_NEVER,
                                                                attributes=ALL_ATTRIBUTES,
                                                                paged_size=Config.LD_PAGE_SIZE, generator=True)
            for entry in entry_generator:
                yield entry

    except Exception as e:
        raise OmmLDAPError(e)

    if ldconn:
        ldconn.unbind()
    if Config.DEBUG:
        log.debug(f'''{cip()}: Disconnect from "{ldconn}"''')


def _connect_ld():
    """Устанавливает подключение к ldap.
    Возвращает указатель подключения
    """

    log = getLogger(Config.APPNAME)
    ldconn = None
    try:
        server = Server(Config.LD_SERVER, use_ssl=True, get_info=ALL)
        ldconn = Connection(server=server, auto_bind=True, user=Config.LD_USER, password=Config.LD_PASS)
    except Exception as e:
        raise OmmLDAPError('LDAP', e)
    if ldconn:
        log.debug(f'''{cip()}: Connect to "{ldconn}"''')
    return ldconn
