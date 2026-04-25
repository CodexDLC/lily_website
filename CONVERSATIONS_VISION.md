# Vision: Codex Communications Module

Transforming the current "Conversations" feature into a standalone, enterprise-grade communication service.

## Core Concept
A unified communication layer for Django projects that handles everything from individual contact form replies to massive marketing campaigns, with a dedicated management UI in the Staff Cabinet.

## 1. Modular Settings (ConversationSettings)
Just like `BookingSettings`, we need a dedicated configuration model:
- **Sender Identity**: Default "From" name and email.
- **Global Signature**: HTML/Text signature appended to all manual replies.
- **Marketing Compliance**: Toggle for double opt-in, unsubscribe link behavior.
- **Templates Registry**: Manage which worker templates are available for which actions.

## 2. Integrated "Mail Client" Experience
- **Unified Inbox**: View messages from all sources (Contact Form, Direct Email, Booking Notes).
- **Threaded Conversations**: Group all messages between the salon and a specific client.
- **Drafts & Templates**: Save frequently used answers as "Quick Replies".
- **Internal Notes**: Leave private staff-only comments on conversation threads.

## 3. Advanced Marketing Campaigns
- **Visual Builder**: Simple UI to compose beautiful emails without touching HTML.
- **Audience Segmentation**: Use the `AudienceFilter` to target specific groups (e.g., "Clients who haven't visited in 3 months").
- **A/B Testing**: Test different subjects to see which performs better.
- **Analytics Dashboard**: Open rates, click rates, and unsubscribe tracking.

## 4. Technical Architecture (The "Codex" Way)
- **Framework Agnostic**: The core logic should live in a library, easily portable to other projects.
- **Worker-First**: All rendering and sending stay in the background (Arq/Redis) to keep the UI snappy.
- **Domain-Driven Translations**: Keep translations separated by domain (`conversations.po`) to avoid the "50KB file" mess.
- **Hook System**: Allow other apps (like `Booking`) to "inject" messages into the conversation history automatically.

## 5. Potential UI Breakdown
- `/cabinet/communications/inbox/` - Daily work with clients.
- `/cabinet/communications/campaigns/` - Marketing work.
- `/cabinet/communications/settings/` - Configuration.

---
*Prepared by Antigravity for Lily Beauty Salon Project*
