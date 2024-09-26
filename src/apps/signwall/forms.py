import datetime

from django import forms
from django.contrib.admin.widgets import AdminDateWidget

from ..arcsubs.models import ArcUser


class RangeDateForm(forms.Form):
    """
        Form de calendarios de busqueda
    """
    start_date = forms.DateField(
        widget=AdminDateWidget,
        initial=datetime.date.today,
        label='Registrados en ARC desde',
        required=True
    )
    end_date = forms.DateField(
        widget=AdminDateWidget,
        initial=datetime.date.today,
        label='Hasta',
        required=False
    )
    domain = forms.ChoiceField(
        required=False,
    )
    device = forms.ChoiceField(
        required=False,
        choices=(
            ('', '- Dispositivo -'),
            ('Desktop', 'Desktop'),
            ('Tablet', 'Tablet'),
            ('Movil', 'Movil'),
            ('unknown', 'Desconocido')
        )
    )
    origin_action = forms.ChoiceField(
        required=False,
        choices=(
            ('', '- Acción -'),
            ('Organico', 'Formulario'),
            ('Signwall', 'Popup signwall'),
            ('Relogin', 'Popup de relogin'),
            ('Mailing', 'Relogin email'),
            ('Premium', 'Popup premium'),
            ('unknown', 'Desconocido')
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['domain'].choices = self.get_domain_choices()

    def get_domain_choices(self):
        try:
            domains = ArcUser.objects.distinct('domain').all().values_list('domain', flat=True)
            choices = [('', '- Dominio -'), ]
            for domain in domains:
                if domain and domain != 'undefined':
                    choice = (domain, domain)
                    choices.append(choice)
            choices.append(('unknown', 'Desconocido'))
            return choices
        except Exception:
            return []
