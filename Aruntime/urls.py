from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from runtime.apps.runtime.views import PlaybookViewSet

run_playbook = PlaybookViewSet.as_view({'post':'run_playbook'})
get_state = PlaybookViewSet.as_view({'post':'get_state'})

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^Aruntime/', run_playbook, name="playbook"),
    url(r'^getstate/', get_state, name="state"),

    ] + static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
