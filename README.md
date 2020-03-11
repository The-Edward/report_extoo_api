# report_extoo_API

API - список всех внешних адресов ОО

##### Использование
Для получения данных необходимо произвести GET запросы к web-серверу.
    
    /extoo/<логин>
    /extooall/
    
Вывод данных происходит в формате JSON.

По-умолчанию выводятся ссылки с доступом к API.

##### Авторизация и защита
Для доступа к ресурсам используется PAM авторизация.

При наличии работающего сервиса vasd на запускаемом сервере будет использоваться доменная авторизация.

Реализована простая защита от DDOS-атак ограничивающая частоту запросов к сервису.  

##### Установка

    pip install -r requrements.txt
    
Либо вручную установить пакеты (остальные будут установлены как зависимости):
* Flask
* envparse
* psycopg2 (psycopg2-binary, если проблемы со сборкой)
* ldap3
* python-pam

##### Настройка
Настройка производится в конфигурационном файле ".env"
Используемые параметры:

    * Общие
    LOG_LEVEL
    APPNAME
    API_HOST
    API_PORT
    OLD_DAYS_LOGINS     : просматривать количество дней, если логин не в сети
    DISABLE_REAL_NAMES  : отключить добавление названий
    PREFIX_OO           : список префиксов ОО для обработки, по-умолчанию все существующие
    REST_TIME           : время "отдыха" между запросами. Для предотвращения DDOS-атаки
    
    * Для подключения к БД
    DB_HOST
    DB_PORT
    DB_BASE
    DB_USER
    DB_PASS
    
    * Для подключения к LDAP
    LD_SERVER
    LD_USER
    LD_PASS
    LD_BASE_DN
    LD_PAGE_SIZE
    

##### Запуск
Запуск реализован через start.sh
Но также можно использовать любой WSGI-сервер, либо нативно (стартовый скрипт: runner.py)
