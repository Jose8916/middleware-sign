from datetime import date, datetime, timedelta
from dateutil import tz, relativedelta
import hashlib
import random
import string
import requests
import pytz


from django.core.mail import EmailMessage
from django.conf import settings
from sentry_sdk import capture_exception
from django.utils.timezone import get_default_timezone


def generate_dmp_hash(email):
    """
        Genera un código para usar en el dmp hash basado en el correo del usuario
    """

    h = hashlib.new('ripemd160')

    dmp = h.update(email.encode('utf-8')).hexdigest()

    return dmp


def generate_dmp_hash_v2(email):
    dmp = ''

    if isinstance(email, str):
        email = email.encode('utf-8')

    try:
        dmp = hashlib.sha256(
            email
        ).hexdigest()

    except Exception:
        capture_exception()

    return dmp


def send_mail(subject, html, to_email, cc, bcc, site):
    resp = EmailMessage(
        subject=subject,
        body=html,
        from_email='%s <%s>' % (site, ''),
        to=[to_email],
        cc=cc,
        bcc=['javier.alarcon2014@gmail.com']
    )
    resp.content_subtype = "html"
    resp.send()
    return resp


def random_characters(stringLength=6):
    lettersAndDigits = string.ascii_lowercase + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))


def search_user_arc(email):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % settings.PAYWALL_ARC_TOKEN,
    }

    url = settings.PAYWALL_ARC_URL + 'identity/api/v1/user?search=email=' + email

    response = requests.get(url, headers=headers)
    return response.json()


def get_profile_user_arc(token, site):
    """
        token: json web token arc
    """
    dict_sites = {
        'elcomercio': settings.PUBLIC_ARC_DOMAIN_COMERCIO,
        'gestion': settings.PUBLIC_ARC_DOMAIN_GESTION,
        'peru21': settings.PUBLIC_ARC_DOMAIN_PERU21
    }

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': '%s' % token,
        }
        if dict_sites.get(site):
            url = dict_sites.get(site) + '/identity/public/v1/profile'
            response = requests.get(url, headers=headers)
            return response.json()
        else:
            return {}
    except Exception as e:
        print(e)
        print('no se encontro al usuario en arc')
        return ''


def search_user_arc_param(type, valor):
    """
        type: tipo de busqueda por email, uuid
        valor : el valor en si
    """
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % settings.PAYWALL_ARC_TOKEN,
        }

        path = "{type}={valor}".format(type=type, valor=valor)
        url = settings.PAYWALL_ARC_URL + 'identity/api/v1/user?search=' + str(path)
        response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        print(e)
        print('no se encontro al usuario en arc')
        return ''


def create_user_arc(email, arc_profile, random_pass, domain, referer, extra_fields, promociones):
    if domain:
        if domain in ['suscripciones.gestion.pe', 'suscripciones.elcomercio.pe']:
            arc_site = domain.split('.')
            arc_site_item = arc_site[1]
        else:
            arc_site = domain.split('.')
            arc_site_item = arc_site[0]

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer %s' % settings.PAYWALL_ARC_TOKEN,
        'Arc-Site': '%s' % arc_site_item
    }
    attributes = [
        {
            'name': 'originDomain',
            'value': domain,
            'type': 'String',
        },
        {
            'name': 'originReferer',
            'value': referer,
            'type': 'String',
        },
        {
            'name': 'originAction',
            'value': 'api',
            'type': 'String',
        },
        {
            'name': 'sendWelcome',
            'value': 'pass',
            'type': 'String',
        },
        {
            'name': 'termsCondPrivaPoli',
            'value': '1',
            'type': 'String',
        }
    ]
    if promociones:
        attributes.append(
                {
                    'name': 'promociones',
                    'value': promociones,
                    'type': 'String',
                }
            )

    if extra_fields:
        for index, value in extra_fields.items():
            if index and value:
                attributes.append(
                    {
                        'name': index,
                        'value': value,
                        'type': 'String',
                    }
                )
        
    arc_profile['attributes'] = attributes
    payload = {
        "identity": {
            "userName": email,
            "credentials": random_pass,
            "grantType": "password"
        },
        "profile": arc_profile,
    }

    url = settings.PAYWALL_ARC_URL + 'identity/api/v1/signup'

    try:
        response = requests.post(url, json=payload, headers=headers)
        result = response.json()

    except Exception:
        capture_exception()

    else:
        return result


def utc_to_lima_time_zone(date_utc):
    if not date_utc:
        return

    try:
        result = get_default_timezone().localize(datetime.strptime("2020-02-18 16:44:41", "%Y-%m-%d %H:%M:%S"))

    except Exception:
        capture_exception()

    else:
        return result


def utc_to_local_time_zone(date_utc):
    if not date_utc:
        return

    try:
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz('America/Lima')

        utc = datetime.strptime(date_utc, '%Y-%m-%d %H:%M:%S')

        # Tell the datetime object that it's in UTC time zone since
        # datetime objects are 'naive' by default
        utc = utc.replace(tzinfo=from_zone)

        # Convert time zone
        local_time = utc.astimezone(to_zone)
    except Exception:
        capture_exception()
    else:
        return local_time


def list_last_month(number):
    date_today = datetime.now(pytz.timezone('America/Lima'))
    month_local = date_today.strftime('%B')
    months = [month_local]
    for i in range(number):
        month_local = date_today - relativedelta.relativedelta(months=i + 1)
        months.append(month_local.strftime('%B'))
    return months
