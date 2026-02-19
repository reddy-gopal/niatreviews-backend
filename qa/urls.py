from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .followup_views import FollowUpListCreateView, FollowUpDetailView
from .feed_views import FeedAnswersView
from .views import QuestionViewSet, FAQListView, question_categories_view
from .search_views import search_questions_view, search_suggestions_view

router = DefaultRouter()
router.register(r"questions", QuestionViewSet, basename="question")

urlpatterns = [
    path("faqs/", FAQListView.as_view(), name="faq-list"),
    path("feed/answers/", FeedAnswersView.as_view(), name="feed-answers"),
    path("questions/categories/", question_categories_view, name="question-categories"),
    path("questions/search/", search_questions_view, name="question-search"),
    path("questions/search/suggestions/", search_suggestions_view, name="question-search-suggestions"),
    path("questions/<slug:slug>/followups/", FollowUpListCreateView.as_view(), name="followup-list-create"),
    path("questions/<slug:slug>/followups/<uuid:pk>/", FollowUpDetailView.as_view(), name="followup-detail"),
    path("", include(router.urls)),
]
