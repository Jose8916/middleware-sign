from django.conf.urls import url

from apps.signwall.api.accounts_transform_to_datamanagemend import ARCToDwhApiView
from apps.signwall.api.accounts_transform_to_datamanagemend_by_uuid import ARCToDwhByUUIApiView
from apps.signwall.api.user_arc import UserArcApiView
from apps.signwall.api.spotim_register_user import SpotimRegisterUserApiView

urlpatterns = [
    url(
        r'^api/userapi-arctodwh/(?P<site_key>(\w)*)$',
        ARCToDwhApiView.as_view(),
        name='arc_to_dwh_apiview'
    ),
    url(
        r'^api/userapi-arctodwh-by-uuid/$',
        ARCToDwhByUUIApiView.as_view(),
        name='arc_to_dwh_apiview'
    ),
    url(
        r'^api/user-exist/$',
        UserArcApiView.as_view(),
        name='user-exist'
    ),
    url(
        r'^api/spotim-register/$',
        SpotimRegisterUserApiView.as_view(),
        name='spotim_register'
    ),
]
