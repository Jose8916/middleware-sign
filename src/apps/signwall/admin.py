from django.contrib import admin

from .models import MppUser, UsersReport, PassArcUser


@admin.register(PassArcUser)
class PassArcUserAdmin(admin.ModelAdmin):
    list_display = ('uuid', )


@admin.register(MppUser)
class MppUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'status')
    list_filter = ('status', )
    search_fields = ('email', )


@admin.register(UsersReport)
class UsersReportAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'state')
    list_filter = ('state', )
