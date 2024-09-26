import random
import re
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, validate_email


def normalize_text(text, style=None):
    text = " ".join(text.strip().split())
    if style:
        try:
            return getattr(text, style)()
        except AttributeError:
            return text
    else:
        return text


def generate_password():
    letters = ['A', 'B', 'C', 'D']
    numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    specials = ['$', '@', '%']
    password_new = str(random.choice(letters)) + str(random.choice(letters)) + '_' + str(random.choice(numbers)) + str(
        random.choice(numbers)) + str(random.choice(specials))
    return password_new


def validar_email(email):
    try:
        validate_email(email)

    except Exception:
        return False

    else:
        return True


def characters_special(string):
    # Make own character set and pass
    # this as argument in compile method
    regex = re.compile('[!#$%^&*()<>?/\|}{~:]')

    # Pass the string in search
    # method of regex object.
    if regex.search(string) == None:
        return True
    else:
        return False