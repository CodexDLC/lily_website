# TASK-SEO-001: Internal Linking & Cross-Service Promotion

## 📋 Overview
To improve SEO ranking and user engagement, we need to implement an internal linking system between services. This will help Google bots discover new pages faster and encourage clients to book multiple services.

## 🎯 Objectives
- Increase the number of indexed pages.
- Improve "Time on Site" by providing relevant links.
- Boost cross-selling (e.g., suggesting hair styling to manicure clients).

## 🛠️ Proposed Implementation

### 1. "Related Services" Block
Add a dynamic block at the bottom of the `service_detail.html` template.
- **Logic:** Show 2-3 services from other categories.
- **Example Text:** "Combine your visit! After your Manicure, enjoy a professional Hair Styling."

### 2. Future Service Teasers
For services that are not yet active for online booking (e.g., "Coming Soon" sections), add a placeholder page with a description.
- **SEO Benefit:** Google starts indexing the keywords before the service is even launched.

### 3. Breadcrumbs Enhancement
Ensure breadcrumbs are present on all service pages:
`Home > Services > Manicure > Gel Nails`

## 📝 Content Strategy (German)
- **Manicure -> Hair:** "Bald auch bei uns: Professionelles Haarstyling. Kombinieren Sie Ihren nächsten Termin!"
- **Hair -> Cosmetics:** "Gönnen Sie Ihrer Haut eine Pause. Entdecken Sie unsere Gesichtsbehandlungen."

## ✅ Definition of Done
- [ ] Related services block added to `service_detail.html`.
- [ ] Internal links are verified to be `index, follow`.
- [ ] Mobile-friendly layout for the new blocks.
- [ ] Tracking added to see how many users click on "Related" links.
