"""Keep denormalized counts and is_answered in sync."""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Question, Answer, QuestionVote, AnswerVote


@receiver(post_save, sender=QuestionVote)
@receiver(post_delete, sender=QuestionVote)
def update_question_vote_counts(sender, instance, **kwargs):
    q = instance.question
    up = QuestionVote.objects.filter(question=q, value=1).count()
    down = QuestionVote.objects.filter(question=q, value=-1).count()
    Question.objects.filter(pk=q.pk).update(upvote_count=up, downvote_count=down)


@receiver(post_save, sender=AnswerVote)
@receiver(post_delete, sender=AnswerVote)
def update_answer_vote_counts(sender, instance, **kwargs):
    a = instance.answer
    up = AnswerVote.objects.filter(answer=a, value=1).count()
    down = AnswerVote.objects.filter(answer=a, value=-1).count()
    Answer.objects.filter(pk=a.pk).update(upvote_count=up, downvote_count=down)


@receiver(post_save, sender=Answer)
def set_question_answered(sender, instance, created, **kwargs):
    if created:
        Question.objects.filter(pk=instance.question_id).update(is_answered=True)


@receiver(post_delete, sender=Answer)
def set_question_unanswered(sender, instance, **kwargs):
    Question.objects.filter(pk=instance.question_id).update(is_answered=False)
