---
name: GitHub push authentication
description: Environment-specific behavior when pushing to GitHub through Replit's GitHub App connection.
---

The GitHub App connection can report as active while the workspace HTTPS askpass credential is rejected by GitHub and no SSH key is available.

**Why:** A repository push was attempted through authenticated HTTPS, the GitHub connector attachment path, and SSH; HTTPS returned GitHub's invalid-token error and SSH returned public-key denial.

**How to apply:** Verify the remote and local commit first, then try the managed Git authentication path once. If it still fails, report the push as blocked rather than changing repository history or asking for a raw token.