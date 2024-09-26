from django.contrib.postgres.fields import JSONField
from django.db import models


from ..webutils.models import _BasicAuditedModel


class MigrationStatus(models.Model):
    data = JSONField(
        null=True,
        blank=True
    )
    processed = models.BooleanField(
        default=False,
        verbose_name='Procesado',
        db_index=True
    )
    register_date = models.DateTimeField(
        null=True,
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Estado de los Usuarios Migrados de MPP'

    def __str__(self):
        return u'%s' % self.register_date


class PassArcUser(_BasicAuditedModel):
    uuid = models.UUIDField(
        blank=True,
        null=True,
        unique=True
    )
    pass_encript = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Password'
    )

    class Meta:
        verbose_name = 'Pass Usuario de ARC'
        verbose_name_plural = 'Pass Usuarios de ARC'


class ArcReport(models.Model):
    REPORT_TYPE_SIGN_UP = 'sign-up-summary'
    REPORT_TYPE_CHOICES = (
        (REPORT_TYPE_SIGN_UP, 'Registros'),
    )
    start_date = models.DateTimeField(
        null=True
    )
    end_date = models.DateTimeField(
        null=True
    )
    report_type = models.CharField(
        max_length=20,
        null=True,
        choices=REPORT_TYPE_CHOICES
    )
    json = models.FileField(
        null=True,
    )


class MppUser(models.Model):
    STATUS_UNKNOWN = 'UNKNOWN'
    STATUS_PENDING = 'PENDING'
    STATUS_IN_PROCESS = 'IN_PROCESS'
    STATUS_MIGRATED = 'MIGRATED'

    STATUS_CHOICES = (
        (STATUS_UNKNOWN, u'Desconocido'),
        (STATUS_PENDING, u'Usuario inactivo'),
        (STATUS_IN_PROCESS, u'Contraseña pendiente'),
        (STATUS_MIGRATED, u'Migración completa'),
    )

    email = models.CharField(
        max_length=128,
        null=True,
        verbose_name='Email',
        unique=True
    )
    csv_profile = JSONField(
        null=True,
        blank=True
    )
    mpp_profile = JSONField(
        null=True,
        blank=True
    )
    arc_profile = JSONField(
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=128,
        verbose_name='Estado',
        null=True,
        blank=True,
        default=None,
        choices=STATUS_CHOICES
    )

    class Meta:
        managed = False
        db_table = 'ecoid_migrateuser'
        verbose_name = u'Usuario de MPP'
        verbose_name_plural = u'Usuarios de MPP'

    def __str__(self):
        return "%s %s" % (self.id, self.email)


# class MppUserStep(models.Model):
#     us_email = models.CharField(
#         max_length=128,
#         null=True,
#         verbose_name='Email',
#         db_index=True,
#     )
#     domain = models.CharField(
#         max_length=128,
#         null=True,
#         verbose_name='Domain',
#     )
#     date_register = models.DateTimeField(
#         blank=True,
#         null=True,
#         verbose_name='Date register',
#     )
#     date_edition = models.DateTimeField(
#         blank=True,
#         null=True,
#         verbose_name='Date edition',
#     )
#     mpp_account_id = models.CharField(
#         max_length=128,
#         null=True,
#         verbose_name='Mpp Account',
#     )
#     arc_account_id = models.CharField(
#         max_length=128,
#         null=True,
#         blank=True,
#         verbose_name='Arc Account',
#     )
#     type = models.CharField(
#         max_length=32,
#         null=True,
#         verbose_name='Type',
#     )
#     content = JSONField(
#         null=True,
#         blank=True
#     )
#     ip = models.CharField(
#         max_length=32,
#         null=True,
#         verbose_name='IP',
#     )
#     referer = models.CharField(
#         max_length=350,
#         null=True,
#         verbose_name='Referer',
#     )
#     user_agent = models.CharField(
#         max_length=350,
#         null=True,
#         verbose_name='User Agent',
#     )
#     origin_data = JSONField(
#         null=True,
#         blank=True
#     )
#     state = models.BooleanField(
#         default=True,
#         verbose_name='State',
#     )

#     class Meta:
#         managed = False
#         db_table = 'ecoid_usercredentials'
#         verbose_name = u'Reactivación de sesion'
#         verbose_name_plural = u'Pasos de reactivación'

#     def __str__(self):
#         return "%s %s" % (self.id, self.us_email)


class UsersReport(models.Model):
    user_profile = JSONField(
        null=True,
        blank=True
    )
    state = models.BooleanField(
        default=True,
        verbose_name='Pendiente'
    )
