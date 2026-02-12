"""
Tests for comment upvotes: ensure upvoting a reply updates only that reply's
upvote_count, not the parent's.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from community.models import Post, Comment, CommentUpvote

User = get_user_model()


class CommentUpvoteReplyTest(TestCase):
    """Confirm reply upvotes update only the reply's upvote_count, not the parent's."""

    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="testpass")
        self.post = Post.objects.create(
            title="Test Post",
            description="Body",
            author=self.user,
        )
        self.parent = Comment.objects.create(
            post=self.post,
            author=self.user,
            parent=None,
            body="Parent comment",
        )
        self.reply = Comment.objects.create(
            post=self.post,
            author=self.user,
            parent=self.parent,
            body="Reply comment",
        )
        self.parent.refresh_from_db()
        self.reply.refresh_from_db()
        self.assertEqual(self.parent.upvote_count, 0)
        self.assertEqual(self.reply.upvote_count, 0)

    def test_upvote_reply_increments_only_reply_count(self):
        """Upvoting the reply must increase only reply.upvote_count, not parent."""
        upvote = CommentUpvote.objects.create(comment=self.reply, user=self.user)

        self.parent.refresh_from_db()
        self.reply.refresh_from_db()
        self.assertEqual(
            self.parent.upvote_count,
            0,
            "Parent upvote_count must be unchanged when upvoting reply",
        )
        self.assertEqual(self.reply.upvote_count, 1, "Reply upvote_count must be 1")

    def test_upvote_parent_increments_only_parent_count(self):
        """Upvoting the parent must increase only parent.upvote_count, not reply."""
        CommentUpvote.objects.create(comment=self.parent, user=self.user)

        self.parent.refresh_from_db()
        self.reply.refresh_from_db()
        self.assertEqual(self.parent.upvote_count, 1, "Parent upvote_count must be 1")
        self.assertEqual(
            self.reply.upvote_count,
            0,
            "Reply upvote_count must be unchanged when upvoting parent",
        )

    def test_both_parent_and_reply_upvotes_independent(self):
        """Parent and reply upvote counts are independent."""
        CommentUpvote.objects.create(comment=self.parent, user=self.user)
        other_user = User.objects.create_user(username="other", password="testpass")
        CommentUpvote.objects.create(comment=self.reply, user=other_user)

        self.parent.refresh_from_db()
        self.reply.refresh_from_db()
        self.assertEqual(self.parent.upvote_count, 1)
        self.assertEqual(self.reply.upvote_count, 1)
