from typing import Any

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies: list[Any] = [
        ("conversations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.CONVERSATIONS_RECIPIENT_MODEL),
    ]

    operations: list[migrations.operations.base.Operation] = [
        migrations.CreateModel(
            name="Campaign",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=500, verbose_name="subject")),
                ("body_text", models.TextField(verbose_name="body text")),
                ("template_key", models.CharField(default="basic", max_length=64, verbose_name="template key")),
                ("locale", models.CharField(db_index=True, default="de", max_length=10, verbose_name="locale")),
                ("body_translations", models.JSONField(blank=True, default=dict, verbose_name="body translations")),
                ("audience_filter", models.JSONField(blank=True, default=dict, verbose_name="audience filter")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("queued", "Queued"),
                            ("sending", "Sending"),
                            ("done", "Done"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=16,
                        verbose_name="status",
                    ),
                ),
                ("status_reason", models.TextField(blank=True, verbose_name="status reason")),
                ("send_at", models.DateTimeField(blank=True, null=True, verbose_name="send at")),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="sent at")),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                ("arq_parent_job_id", models.CharField(blank=True, max_length=128, verbose_name="arq parent job id")),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="campaigns_created",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
            ],
            options={
                "verbose_name": "Email Campaign",
                "verbose_name_plural": "Email Campaigns",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CampaignRecipient",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("email", models.EmailField(verbose_name="email")),
                ("first_name", models.CharField(blank=True, max_length=255, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=255, verbose_name="last name")),
                ("locale", models.CharField(default="de", max_length=10, verbose_name="locale")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("sent", "Sent"),
                            ("failed", "Failed"),
                            ("bounced", "Bounced"),
                            ("unsubscribed", "Unsubscribed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=16,
                        verbose_name="status",
                    ),
                ),
                ("arq_job_id", models.CharField(blank=True, max_length=128, verbose_name="arq job id")),
                ("sent_at", models.DateTimeField(blank=True, null=True, verbose_name="sent at")),
                ("error", models.TextField(blank=True, verbose_name="error")),
                (
                    "campaign",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="recipients",
                        to="conversations.campaign",
                        verbose_name="campaign",
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="campaign_entries",
                        to=settings.CONVERSATIONS_RECIPIENT_MODEL,
                        verbose_name="recipient",
                    ),
                ),
            ],
            options={
                "verbose_name": "Campaign Recipient",
                "verbose_name_plural": "Campaign Recipients",
            },
        ),
        migrations.AddIndex(
            model_name="campaignrecipient",
            index=models.Index(fields=["campaign", "status"], name="conversatio_campaig_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="campaignrecipient",
            unique_together={("campaign", "recipient")},
        ),
    ]
