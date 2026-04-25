from django.urls import path

from ..views.campaigns import (
    AudienceCountView,
    CampaignCreateView,
    CampaignDeleteView,
    CampaignDetailView,
    CampaignListView,
)

campaigns_urlpatterns = [
    path("conversations/campaigns/", CampaignListView.as_view(), name="conversations_campaigns"),
    path("conversations/campaigns/new/", CampaignCreateView.as_view(), name="conversations_campaigns_new"),
    path(
        "conversations/campaigns/audience-count/",
        AudienceCountView.as_view(),
        name="conversations_campaigns_audience_count",
    ),
    path("conversations/campaigns/<int:pk>/", CampaignDetailView.as_view(), name="conversations_campaigns_detail"),
    path(
        "conversations/campaigns/<int:pk>/delete/", CampaignDeleteView.as_view(), name="conversations_campaigns_delete"
    ),
]
