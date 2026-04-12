# Python modules
from datetime import datetime
from random import choice, choices
from typing import Any

# Django modules
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.db.models import QuerySet

# Project modules
from apps.users.models import CustomUser
from apps.blog.models import Category, Post, Tag, Status, Comment


class Command(BaseCommand):
    help = "Generate fake data for testing purposes"

    EMAIL_DOMAINS = (
        "example.com",
        "test.com",
        "sample.org",
        "demo.net",
        "mail.com",
    )
    SOME_WORDS = (
        "lorem",
        "ipsum",
        "dolor",
        "sit",
        "amet",
        "consectetur",
        "adipiscing",
        "elit",
        "sed",
        "do",
        "eiusmod",
        "tempor",
        "incididunt",
        "ut",
        "labore",
        "et",
        "dolore",
        "magna",
        "aliqua",
    )

    def __generate_users(self, user_count: int = 30) -> None:
        """
        Generates users for testing purposes.
        """

        USER_PASSWORD = make_password(password="12345")
        created_users: list[CustomUser] = []
        users_before: int = CustomUser.objects.count()

        for i in range(user_count):
            username: str = f"user{i + 1}"
            email: str = f"user{i + 1}@{choice(self.EMAIL_DOMAINS)}"
            first_name: str = choice(self.SOME_WORDS).capitalize()
            last_name: str = choice(self.SOME_WORDS).capitalize()
            created_users.append(
                CustomUser(
                    username=username,
                    email=email,
                    password=USER_PASSWORD,
                    first_name=first_name,
                    last_name=last_name,
                )
            )

        CustomUser.objects.bulk_create(created_users, ignore_conflicts=True)
        users_after: int = CustomUser.objects.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {users_after - users_before} CustomUser records."
            )
        )

    def __generate_categories(self, category_count: int = 30) -> None:
        """
        Generates categories for testing purposes.
        """

        created_categories: list[Category] = []
        before: int = Category.objects.count()

        for i in range(category_count):
            name_en: str = choice(self.SOME_WORDS).capitalize()
            created_categories.append(
                Category(
                    name_en=name_en,
                    slug=f"{name_en}_{i}",
                )
            )

        Category.objects.bulk_create(created_categories, ignore_conflicts=True)
        after: int = Category.objects.count()

        self.stdout.write(
            self.style.SUCCESS(f"Created {after - before} Category records.")
        )

    def __generate_tags(self, tag_count: int = 15) -> None:
        """
        Generates tags for testing purposes.
        """

        created_tags: list[Tag] = []
        before: int = Tag.objects.count()

        for i in range(tag_count):
            name: str = "tag_" + choice(self.SOME_WORDS).capitalize()
            created_tags.append(
                Tag(
                    name=name,
                    slug=f"{name}_{i}",
                )
            )

        Tag.objects.bulk_create(created_tags, ignore_conflicts=True)
        after: int = Tag.objects.count()

        self.stdout.write(
            self.style.SUCCESS(f"Created {after - before} Tags records.")
        )

    def __generate_posts(self, post_count: int = 30) -> None:
        """
        Generates posts for testing purposes.
        """

        created_posts: list[Post] = []
        before: int = Post.objects.count()

        categories: QuerySet[Category] = Category.objects.all()
        authors: QuerySet[CustomUser] = CustomUser.objects.all()

        for i in range(post_count):
            title: str = " ".join(choices(self.SOME_WORDS, k=2)).capitalize()
            created_posts.append(
                Post(
                    category=choice(categories),
                    author=choice(authors),
                    title=title,
                    body=f"Description for {title}",
                    status=choice(Status.choices),
                    slug=f"{title}_{i}",
                )
            )

        Post.objects.bulk_create(created_posts, ignore_conflicts=True)
        after: int = Post.objects.count()

        self.stdout.write(
            self.style.SUCCESS(f"Created {after - before} Posts records.")
        )

    def __generate_comments(self, comment_count: int = 20) -> None:
        """
        Generates Comments for testing purposes.
        """

        created_comments: list[Comment] = []
        before: int = Comment.objects.count()

        posts: QuerySet[Post] = Post.objects.all()
        authors: QuerySet[CustomUser] = CustomUser.objects.all()

        for i in range(comment_count):
            created_comments.append(
                Comment(
                    post=choice(posts),
                    author=choice(authors),
                    body=f"Comment #0{i}",
                )
            )

        Comment.objects.bulk_create(created_comments, ignore_conflicts=True)
        after: int = Comment.objects.count()

        self.stdout.write(
            self.style.SUCCESS(f"Created {after - before} Comment records.")
        )

    def handle(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        """Command entry point."""

        start_time: datetime = datetime.now()

        self.__generate_users()
        self.__generate_categories()
        self.__generate_posts()
        self.__generate_tags()
        self.__generate_comments()

        self.stdout.write(
            "The whole process to generate data took: {} seconds".format(
                (datetime.now() - start_time).total_seconds()
            )
        )
