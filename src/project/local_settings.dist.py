
###########
# PROJECT #
###########

DEBUG = False

ALLOWED_HOSTS = ['devarc.comerciosuscripciones.pe', ]

ENVIRONMENT = 'test'

SENTRY_DNS = 'https://5c710c4738934c48bd8cc3fa20a35d74@sentry.ec.pe/66'

# DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'middleware_prod_viernes',
        'USER': 'postgres',
        'PASSWORD': '123',
        'HOST': 'localhost',
        'PORT': '5432',
    },
    'migration': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'newdatabase',
        'USER': 'postgres',
        'PASSWORD': '123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

EMAIL_USE_TLS = True
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'juan.perez@gmail.com'
EMAIL_HOST_PASSWORD = '*****'
EMAIL_PORT = 587


###########
# PAYWALL #
###########

# MPP
PAYWALL_MPP_CLIENT_ID = "5056"
PAYWALL_MPP_DOMAIN = "https://us1-api-uat.mppglobal.com"
PAYWALL_MPP_PASSWORD = "x8HPj7r2C6MwAc"
PAYWALL_MPP_TOKEN = "26FE4C6B11FF48499E97EAFF05115BC6"
PAYWALL_MPP_URL = "https://us1-api-uat.mppglobal.com/rest/"
PAYWALL_MPP_VERSION = "10.0.0"

# SIEBEL
PAYWALL_SIEBEL_DOMAIN = 'http://200.4.199.84'
PAYWALL_SIEBEL_URL = 'http://200.4.199.84/wssuscripcionsiebel/'

# ARC
PAYWALL_ARC_URL = 'https://api.sandbox.elcomercio.arcpublishing.com/'
PAYWALL_ARC_TOKEN = '56V58QFSB7EC6DC6EAFUDC34S04T4L18pnJapmry/XUSQSmXuTFWu4ZfJlYHcL9+EP98++sT'

CONFIG = {
    'elcomercio': {
        'url': 'http://127.0.0.1:8000',
        'EMAIL': {
            'FROM': 'info@elcomercio.pe',
            'BCC': ['joaquin.tarazona@ec.pe'],
        }
    }
}


##################
# DATA WAREHOUSE #
##################

DOMAIN_DIC = {
    "a94a8fe5ccb19ba61c4c0873d391e987982fbbd3": "elcomercio.pe",
    "108f85a3d8e750a325ced951af6cd758a90e73a34": "pre01.gestion.pe"
}
