from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authtoken.views import obtain_auth_token

from apps.signwall.views.views import UserByDateReport, UsersRepeatedReport, DisplayNameRepeatedReport
from apps.signwall.views.report_by_range_users import UserByRangeReport
from apps.signwall.views.date_activate_account import VerifiedUsers
from apps.signwall.body_dashboard_view import BodyDashboard


urlpatterns = [

    path(
        'admin/body_dashboard',
        BodyDashboard.as_view(),
        name="body_dashboard"
    ),
    path(
        'admin/verified_users',
        VerifiedUsers.as_view(),
        name="verified_users"
    ),
    path(
        'admin/arc/status',
        UserByDateReport.as_view(),
        name="userbydate"
    ),
    path(
        'admin/arc/total',
        UserByRangeReport.as_view(),
        name="userbyrange"
    ),
    path(
        'admin/arc/user_repeated',
        UsersRepeatedReport.as_view(),
        name="user_repeated"
    ),
    path(
        'admin/arc/display_name_repeated',
        DisplayNameRepeatedReport.as_view(),
        name="display_name_repeated"
    ),
    path(
        'admin/',
        admin.site.urls
    ),
    # APIs
    path('', include('apps.signwall.api.urls')),
]


if settings.ENVIRONMENT != 'production':
    schema_view = get_schema_view(
        openapi.Info(
            title="Signwall • Middleware",
            default_version='v0.9',
            description="APIs de integración de signwall-middleware.",
            # terms_of_service="https://www.google.com/policies/terms/",
            # contact=openapi.Contact(email="contact@snippets.local"),
            # license=openapi.License(name="BSD License"),
        ),
        public=True,
        permission_classes=(permissions.IsAuthenticated,),
    )

    urlpatterns = [
        path(
            '',
            RedirectView.as_view(url='/admin/', permanent=False),
            name="index"
        ),
        # API
        path(
            'api-token-auth/',
            obtain_auth_token,
            name='api_token_auth'
        ),
        # DOCS
        url(
            r'^swagger(?P<format>\.json|\.yaml)$',
            schema_view.without_ui(cache_timeout=0),
            name='schema-json'
        ),
        url(
            r'^swagger/$',
            schema_view.with_ui('swagger', cache_timeout=0),
            name='schema-swagger-ui'
        ),
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns


if settings.DEBUG:
    try:
        import debug_toolbar
    except Exception:
        pass
    else:
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns


admin.site.site_header = 'Signwall • Middleware'
admin.site.site_title = 'Signwall • Middleware'
