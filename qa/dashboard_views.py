"""
Senior dashboard: GET /api/dashboard/senior/ — only for verified seniors.
"""
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Sum

from .models import Answer, FollowUp, Question
from .serializers import FollowUpSerializer, QuestionListSerializer
from .views import _user_is_verified_senior


def error_response(code: str, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
    return Response({"code": code, "detail": detail}, status=status_code)


class SeniorDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not _user_is_verified_senior(request.user):
            return error_response(
                "FORBIDDEN",
                "Only verified seniors can access the senior dashboard.",
                status.HTTP_403_FORBIDDEN,
            )
        user = request.user

        my_answers_total = Answer.objects.filter(author=user).count()
        pending_questions = list(
            Question.objects.filter(is_answered=False)
            .select_related("author")
            .order_by("-created_at")[:10]
        )
        pending_serializer = QuestionListSerializer(
            pending_questions,
            many=True,
            context={"request": request},
        )

        # Recent follow-ups on questions this senior has answered
        my_answer_question_ids = Answer.objects.filter(author=user).values_list("question_id", flat=True)
        recent_followups = list(
            FollowUp.objects.filter(question_id__in=my_answer_question_ids)
            .select_related("author", "question")
            .order_by("-created_at")[:10]
        )
        followups_data = FollowUpSerializer(
            recent_followups,
            many=True,
            context={"request": request},
        ).data
        for i, fu in enumerate(recent_followups):
            followups_data[i]["question_slug"] = fu.question.slug

        answer_upvotes_total = (
            Answer.objects.filter(author=user).aggregate(Sum("upvote_count"))["upvote_count__sum"] or 0
        )

        try:
            follower_count = user.senior_profile.follower_count
        except Exception:
            follower_count = 0

        return Response({
            "my_answers": {"total": my_answers_total},
            "pending_questions": pending_serializer.data,
            "follower_count": follower_count,
            "recent_followups": followups_data,
            "answer_upvotes_total": answer_upvotes_total,
        })
