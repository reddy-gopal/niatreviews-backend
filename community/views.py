import logging
from django.db.models import OuterRef, Subquery
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Category, Tag, Post, Comment, PostVote, CommentUpvote
from .permissions import IsAuthorOrReadOnly, SeniorMustCompleteOnboarding
from .pagination import PostCursorPagination, CommentCursorPagination
from .serializers import (
    CategorySerializer,
    TagSerializer,
    PostSerializer,
    CommentSerializer,
    CommentUpvoteSerializer,
)

logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
    pagination_class = None  # list is small; default CursorPagination uses "created", model has "created_at"
    permission_classes = [IsAuthenticatedOrReadOnly, SeniorMustCompleteOnboarding]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [IsAuthenticatedOrReadOnly, SeniorMustCompleteOnboarding]


class PostViewSet(viewsets.ModelViewSet):
    queryset = (
        Post.objects.select_related("author", "category")
        .prefetch_related("tags")
        .order_by("-created_at")
    )
    serializer_class = PostSerializer
    pagination_class = PostCursorPagination
    lookup_field = "slug"
    lookup_url_kwarg = "slug"
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly, SeniorMustCompleteOnboarding]

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__slug=category)
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__slug=tag)
        author = self.request.query_params.get("author")
        if author:
            qs = qs.filter(author_id=author)
        upvoted_by = self.request.query_params.get("upvoted_by")
        if upvoted_by == "me" and self.request.user.is_authenticated:
            qs = qs.filter(votes__user=self.request.user, votes__value=PostVote.VALUE_UP).distinct()
        downvoted_by = self.request.query_params.get("downvoted_by")
        if downvoted_by == "me" and self.request.user.is_authenticated:
            qs = qs.filter(votes__user=self.request.user, votes__value=PostVote.VALUE_DOWN).distinct()
        # Annotate user_vote to avoid N+1 in serializer (production-safe)
        if self.request.user.is_authenticated:
            my_vote = PostVote.objects.filter(
                post=OuterRef("pk"),
                user=self.request.user,
            ).values("value")[:1]
            qs = qs.annotate(user_vote=Subquery(my_vote))
        return qs.distinct() if (tag or upvoted_by == "me" or downvoted_by == "me") else qs

    def _vote_response(self, post, user):
        """Build vote response with counts and current user_vote."""
        vote = PostVote.objects.filter(post_id=post.id, user=user).first()
        user_vote = vote.value if vote else None
        return {
            "upvote_count": post.upvote_count,
            "downvote_count": post.downvote_count,
            "user_vote": user_vote,
        }

    @action(detail=True, methods=["post", "delete"], url_path="upvote")
    def upvote(self, request, slug=None):
        """POST: set vote to upvote (1). DELETE: remove vote. Requires auth."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required to upvote."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        post = self.get_object()
        user = request.user
        if request.method == "POST":
            _, created = PostVote.objects.update_or_create(
                post_id=post.id,
                user=user,
                defaults={"value": PostVote.VALUE_UP},
            )
            post.refresh_from_db()
            return Response(
                {**self._vote_response(post, user), "upvoted": True},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        PostVote.objects.filter(post_id=post.id, user=user).delete()
        post.refresh_from_db()
        return Response(
            {**self._vote_response(post, user), "upvoted": False},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post", "delete"], url_path="downvote")
    def downvote(self, request, slug=None):
        """POST: set vote to downvote (-1). DELETE: remove vote. Requires auth."""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required to downvote."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        post = self.get_object()
        user = request.user
        if request.method == "POST":
            _, created = PostVote.objects.update_or_create(
                post_id=post.id,
                user=user,
                defaults={"value": PostVote.VALUE_DOWN},
            )
            post.refresh_from_db()
            return Response(
                {**self._vote_response(post, user), "downvoted": True},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        PostVote.objects.filter(post_id=post.id, user=user).delete()
        post.refresh_from_db()
        return Response(
            {**self._vote_response(post, user), "downvoted": False},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="comments")
    def comments_list(self, request, slug=None):
        """GET /api/posts/:slug/comments/ — paginated comments for this post."""
        post = self.get_object()
        comments = (
            Comment.objects.filter(post=post)
            .select_related("author", "parent")
            .order_by("created_at")
        )
        paginator = CommentCursorPagination()
        page = paginator.paginate_queryset(comments, request, view=self)
        if page is not None:
            serializer = CommentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = (
        Comment.objects.select_related("author", "parent", "post")
        .prefetch_related("replies")
        .order_by("-created_at")
    )
    serializer_class = CommentSerializer
    pagination_class = CommentCursorPagination
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly, SeniorMustCompleteOnboarding]

    def get_queryset(self):
        qs = super().get_queryset()
        post_id = self.request.query_params.get("post")
        if post_id:
            qs = qs.filter(post_id=post_id)
        author = self.request.query_params.get("author")
        if author:
            qs = qs.filter(author_id=author)
        upvoted_by = self.request.query_params.get("upvoted_by")
        if upvoted_by == "me" and self.request.user.is_authenticated:
            qs = qs.filter(upvotes__user=self.request.user).distinct()
        return qs

    @action(detail=True, methods=["post", "delete"], url_path="upvote")
    def upvote(self, request, pk=None):
        """
        Toggle upvote for the comment identified by URL pk (this comment only, never parent).
        POST: add upvote. DELETE: remove upvote.
        comment_id in URL is the source of truth (reply or top-level).
        """
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required to upvote."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        comment = self.get_object()
        comment_id = str(comment.id)
        user = request.user
        logger.info(
            "Comment upvote action: comment_id=%s (parent_id=%s) user_id=%s method=%s",
            comment_id,
            str(comment.parent_id) if comment.parent_id else None,
            getattr(user, "id", None),
            request.method,
        )
        if request.method == "POST":
            _, created = CommentUpvote.objects.get_or_create(
                comment_id=comment.id,
                user=user,
                defaults={"comment_id": comment.id, "user": user},
            )
            if created:
                logger.debug("Comment upvote created: comment_id=%s", comment_id)
            return Response(
                {"upvoted": True, "upvote_count": Comment.objects.get(id=comment.id).upvote_count},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        else:
            deleted, _ = CommentUpvote.objects.filter(comment_id=comment.id, user=user).delete()
            if deleted:
                logger.debug("Comment upvote removed: comment_id=%s", comment_id)
            return Response(
                {"upvoted": False, "upvote_count": Comment.objects.get(id=comment.id).upvote_count},
                status=status.HTTP_204_NO_CONTENT,
            )


class CommentUpvoteViewSet(viewsets.ModelViewSet):
    """
    List/create/delete comment upvotes.
    Prefer POST /api/comments/<comment_id>/upvote/ so comment_id comes from URL (reply or parent).
    Or POST /api/comment-upvotes/ with body {"comment": "<exact_comment_uuid>"}.
    """
    serializer_class = CommentUpvoteSerializer
    queryset = CommentUpvote.objects.select_related("comment", "user").order_by("-created_at")
    permission_classes = [IsAuthenticatedOrReadOnly, SeniorMustCompleteOnboarding]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        comment_id = self.kwargs.get("comment_id")
        if comment_id:
            context["comment"] = Comment.objects.get(id=comment_id)
        return context

    def get_queryset(self):
        qs = super().get_queryset()
        comment_id = self.kwargs.get("comment_id")
        if comment_id:
            qs = qs.filter(comment_id=comment_id)
        return qs

    def perform_create(self, serializer):
        comment = serializer.validated_data["comment"]
        logger.info(
            "CommentUpvote perform_create: comment_id=%s user_id=%s (exact comment, not parent)",
            comment.id,
            self.request.user.id,
        )
        serializer.save(user=self.request.user)