"""webpanel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home)
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view())
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView

from webpanel.views import views
from webpanel.views import views_logs as logs_views, views_visuals as visuals_views, views_health as health_views, \
    views_data as data_views, views_strategies as strategy_views

urlpatterns = [
    # Auth endpoint.
    path('api/token/new', TokenObtainPairView.as_view()),
    path('api/token/refresh', TokenRefreshView.as_view()),

    # Update endpoint.
    path('api/update', views.update),

    # Logs endpoint.
    path('api/logs/logfile/', logs_views.logfile),
    path('api/logs/logfeed_filenames/', logs_views.logfeed_filenames),
    path('api/logs/latest/', logs_views.latest_messages),
    path('api/logs/delete', logs_views.clear_logs),

    # Visuals endpoint.
    path('api/visuals/get/', visuals_views.get_visual_data),
    path('api/visuals/generate/', visuals_views.generate_visual),

    # Health checks endpoint.
    path('api/health_checks/get/', health_views.get_check_result),
    path('api/health_checks/perform/', health_views.perform_check),

    # Data endpoint.
    path('api/data/patch/', data_views.patch_data),
    path('api/data/heal', data_views.heal_data),
    path('api/data/reset_collection_attempts', data_views.reset_collection_attempts),
    path('api/data/is_patching', data_views.is_patching),
    path('api/data/is_healing', data_views.is_healing),
    path('api/data/status', data_views.get_data_status),
    path('api/data/reset_trade_history', data_views.reset_trade_history),
    path('api/data/symbols', data_views.get_symbols),
    path('api/data/dates/<symbol>', data_views.get_dates),
    path('api/data/warmup_day_options/', data_views.get_warmup_day_options),
    path('api/data/get_simulation_output', data_views.get_simulation_output),

    # Strategy endpoint.
    path('api/strategy/get_day_strategies', strategy_views.get_day_strategies),
    path('api/strategy/get_swing_strategies', strategy_views.get_swing_strategies),
    path('api/strategy/simulate_day_strategy/', strategy_views.simulate_day_strategy),
    path('api/strategy/is_running_simulation', strategy_views.is_running_simulation),

    # All other urls.
    path('', views.do_nothing, {'resource': ''}),
    path('<path:resource>', views.do_nothing)
]
