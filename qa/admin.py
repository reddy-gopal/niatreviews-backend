from django.contrib import admin
from .models import Question, Answer, QuestionVote, AnswerVote, FollowUp


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "category_confidence", "category_source", "is_answered", "is_faq", "faq_order", "upvote_count", "created_at"]
    list_filter = ["is_answered", "is_faq", "category", "category_source"]
    search_fields = ["title", "body"]
    ordering = ["-created_at"]
    readonly_fields = ["category_confidence", "category_source"]
    actions = ["mark_as_faq", "unmark_faq"]

    @admin.action(description="Mark as FAQ")
    def mark_as_faq(self, request, queryset):
        from django.db.models import Max
        max_order = Question.objects.filter(is_faq=True).aggregate(m=Max("faq_order"))
        next_order = (max_order.get("m") or 0) + 1
        for i, q in enumerate(queryset):
            q.is_faq = True
            q.faq_order = next_order + i
            q.save(update_fields=["is_faq", "faq_order"])

    @admin.action(description="Remove from FAQ")
    def unmark_faq(self, request, queryset):
        queryset.update(is_faq=False, faq_order=0)


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ["question", "author", "created_at"]
    search_fields = ["body"]
    raw_id_fields = ["question", "author"]
    list_filter = ["created_at"]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["question", "author", "upvote_count", "created_at"]
    search_fields = ["body"]
    raw_id_fields = ["question", "author"]


@admin.register(QuestionVote)
class QuestionVoteAdmin(admin.ModelAdmin):
    list_display = ["question", "user", "value"]
    raw_id_fields = ["question", "user"]


@admin.register(AnswerVote)
class AnswerVoteAdmin(admin.ModelAdmin):
    list_display = ["answer", "user", "value"]
    raw_id_fields = ["answer", "user"]
