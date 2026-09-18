# Google review integration status

The current redesign displays the historical customer-story corpus from `mhsrv-reviews-all.json`, without inferred star ratings. It does not display the old seeded `google-reviews.json` data or claim a live Google review feed.

`fetch-google-reviews.js` is retained as an earlier integration reference. A future Google Business Profile or Places integration requires authorized credentials, current API documentation, source attribution, and a decision about appropriate display and caching. Keep credentials out of the public site. Never assign five stars to a story without an explicit source rating.
