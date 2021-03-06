from django.urls import re_path
from .views import *


urlpatterns = [
    re_path(r'^api/v1/tanalyzer/getauthtoken/$', GetAuthTokenView.as_view()),
    re_path(r'^api/v1/tanalyzer/getboardlist/$', GetBoardListView.as_view()),
    re_path(r'^api/v1/tanalyzer/createboard/$', CreateBoardView.as_view()),
    re_path(r'^api/v1/tanalyzer/analyze/$', AnalyzeView.as_view()),
    re_path(r'^api/v1/tanalyzer/milestones/$', MilestonesView.as_view()),
    re_path(r'^api/v1/tanalyzer/results/$', AnalysisResultsPollView.as_view())
]
