from django.urls import re_path
from .views import *


urlpatterns = [
    re_path(r'^api/v1/ganalyzer/listrepository/$', ListRepositoryView.as_view()),
    re_path(r'^api/v1/ganalyzer/createrepository/$', CreateRepositoryView.as_view()),
    re_path(r'^api/v1/ganalyzer/flightcheck/$', FlightCheckView.as_view()),
    re_path(r'^api/v1/ganalyzer/analyze/$', AnalyzeView.as_view()),
    re_path(r'^api/v1/ganalyzer/results/$', AnalysisResultsPollView.as_view())
]
