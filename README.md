# MHSRV Redesign — Full Site

23 real units from the live Blue Compass Alvarado feed, each with its own VDP in /units. On-site reviews hub (reviews.html) + individual review pages in /reviews with Review schema. Forms deliver to ebendele@gmail.com via FormSubmit (one-time activation email on first submission).

Production swaps: data.js → live inventory API; reviews-data.js → WordPress REST import of all 4,571 reviews with 301s from motorhomespecialistreviews.com.

Shared footer: footer.js renders the site footer (locations + legal & pricing disclaimer) on every page — edit footer.js once and all ~5,800 pages update. Pages include it with `<script src="footer.js" defer></script>` (`../footer.js` from /units and /reviews). On pages with the fixed bottom dock it extends the dark footer beneath the dock so no background gap shows.
