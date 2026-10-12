# Backlog: .communicatio MVP

## 1. Empty Django project with a passing test
Goal: A runnable Django project managed by uv, with a home page and one passing test.
Description: Create the project with `uv`, add pytest-django and ruff, a `core` app and a home page that returns 200. Add one test that checks the home page.

## 2. Base layout, HTMX and mobile-friendly styling
Goal: Every page shares one responsive layout that works on a phone screen.
Description: Add a base template with navigation, a viewport meta tag, HTMX loaded, and simple responsive CSS. Include a place to show flash messages.

## 3. Custom user model and registration
Goal: A visitor can register with an email, a nickname and a password.
Description: Add a custom user model that uses email as the login field, a nickname field, and `is_email_verified` set to false by default. Add a registration page with validation errors.

## 4. Email verification
Goal: A registered user must confirm their email through a link before using the app.
Description: Send a verification email with a signed token on registration (console backend in development). Add the confirmation view and a "resend link" action.

## 5. Login, logout and the verification gate
Goal: Users can log in and out, and unverified users are blocked from the app pages.
Description: Add login and logout views and a mixin that redirects unverified users to a "please verify your email" page.

## 6. Profile with privacy settings
Goal: A user has a profile where every field can be made public or hidden, hidden by default.
Description: Add a profile model (display name, city, about) with a visibility flag per field, an edit page, and a helper that returns only the public fields of a profile for other users.

## 7. Survey questions managed in admin
Goal: An admin can create survey questions and answer options in Django admin.
Description: Add models for survey question and answer option, register them in admin, and add a data migration with 6 starter questions.

## 8. Taking the survey
Goal: A verified user answers the survey and the answers are saved as their interest profile.
Description: Add a survey page with all questions, save the selected options per user, allow retaking, and redirect to the results after saving.

## 9. Groups: model, creation and approval status
Goal: A user can create a group, which stays hidden until an admin approves it.
Description: Add a group model with name, description, topic options, owner and status `PENDING`, `APPROVED` or `REJECTED`. Add a create page and a "my groups" page that shows the status to the owner.

## 10. Admin approves or rejects groups
Goal: An admin can approve or reject pending groups from Django admin.
Description: Add admin actions and a filter by status. Approving sets `APPROVED`, rejecting sets `REJECTED` with an optional reason shown to the owner.

## 11. Group matching results
Goal: After the survey a user sees approved groups ranked by match percentage.
Description: Add a matching function that compares the survey answers with the group topics and returns a percentage. Show only `APPROVED` groups, sorted by percentage, with a join button.

## 12. People matching results
Goal: After the survey a user sees other users with similar answers, respecting privacy settings.
Description: Reuse the matching function for users. Show only nickname and the profile fields the other user made public, with a match percentage and a "send request" button.

## 13. Joining groups and group membership
Goal: A verified user can join and leave an approved group, and members see the member list.
Description: Add a membership model, join and leave actions, and a group detail page. The member list shows only nicknames and public profile fields.

## 14. Connection requests between people
Goal: A user can send a request to another user, who can accept or decline it.
Description: Add a request model with `PENDING`, `ACCEPTED`, `DECLINED`. Add inbox, accept and decline actions. Block duplicate requests and requests to oneself.

## 15. Direct chat
Goal: Two users with an accepted request can exchange messages.
Description: Add a message model and a chat page that refreshes with HTMX polling every few seconds. Only the two users can open the chat.

## 16. Group chat
Goal: Members of a group can exchange messages inside the group.
Description: Reuse the chat approach for groups. Only members can read and write, and leaving the group removes access.

## 17. Offline meetups: create and confirm attendance
Goal: A group owner can schedule a meetup and members can confirm attendance.
Description: Add a meetup model (date, place, description), a create page for the owner, a list on the group page, and an "I'm going" toggle. Show a safety notice about meeting in public places.

## 18. Report button
Goal: A user can report another user, a group or a message to the admins.
Description: Add a report model with target, reason and status `OPEN` or `RESOLVED`. Add a report button on profiles, group pages and chats, with a short form.

## 19. Admin reviews reports and blocks
Goal: An admin can review reports and block a user or a group.
Description: Register reports in admin with filters, add actions to block the reported user or group, and make blocked users unable to log in and blocked groups disappear from results.

## 20. Native mobile app (post-MVP)
Goal: Record the native iOS/Android app as the next stage after the MVP.
Description: Placeholder for a future task. It is out of scope for the MVP and is only filed so that it is not forgotten.
