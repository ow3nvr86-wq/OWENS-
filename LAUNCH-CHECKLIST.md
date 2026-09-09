# Court Craft — App Store launch checklist

Status as of 9 September 2026. Tick items off in order; the blockers come first.

## Blockers (nothing ships until these are done)

- [ ] **Decide the final name.** Court Craft looks clear on the App Store. Porcraft is not
      recommended: porcraft.com exists and a Por Craft creator already holds the TikTok and
      YouTube handles, which hurts the marketing plan.
- [ ] **Rebuild the app from source.** Only the compiled web build exists today. The App
      Store needs a native iOS build, which has to come from an Expo/React Native project.
- [ ] **Replace the fake paywall with real In-App Purchase.** Today `purchase()` writes a
      flag to local storage and unlocks. No StoreKit, no RevenueCat, no payment code of any
      kind. Apple rejects this under Guideline 3.1.1 (payments must use IAP) and Guideline
      2.1 (app completeness).
- [ ] **Apple Developer Program enrolment.** Must be held by someone 18 or over. Allow one
      to two days for approval.

## Money setup (App Store Connect, after enrolment)

- [ ] Sign the **Paid Applications Agreement** under Business.
- [ ] Complete **tax forms** (W-9 in the US, W-8BEN outside it).
- [ ] Add **bank details**. Apple pays into this account, monthly, roughly 30 to 45 days
      after the end of each month.
- [ ] Apply to the **App Store Small Business Program**. Commission drops from 30% to 15%
      while revenue stays under one million dollars a year. Free to join, worth doing on
      day one.
- [ ] Create the three products to match the paywall: yearly subscription, monthly
      subscription, lifetime non-consumable unlock.

## Legal and store listing

- [x] Privacy policy written — `docs/privacy.html`
- [x] Terms of use written — `docs/terms.html`
- [ ] **Add a contact email** to both pages, replacing `[ADD YOUR CONTACT EMAIL HERE]`.
- [ ] **Enable GitHub Pages** so both pages are publicly reachable: repo Settings → Pages →
      Source: Deploy from a branch → Branch `claude/new-session-v8qhxu`, folder `/docs` → Save.
- [ ] Point the app's two policy links at the live URLs. They currently point at
      `courtready.app`, which is the old name and not owned.
- [ ] Paste the privacy URL into App Store Connect. Review checks that it opens.
- [ ] Fill in the **App Privacy** questionnaire. Answer is "Data Not Collected" — verified by
      auditing every outbound address in the build.
- [ ] Set age rating to **12+**. Do not opt into the Kids Category; it triggers far stricter rules.
- [ ] Show auto-renewal wording on the paywall screen itself, next to the price.

## Already verified

- No analytics, tracking, advertising or backend server of any kind.
- Health and injury disclaimers are present and strong.
- App runs cleanly at iPhone screen size with no JavaScript errors.
