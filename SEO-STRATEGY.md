# MHSRV production SEO migration

The GitHub site is a **noindex design preview**. The established production site remains at https://mhsrv.com/. No traffic, ranking, backlink or conversion outcome is guaranteed by this redesign.

## Implemented foundation

- Crawlable static unit descriptions and specifications, stable existing unit/review paths, category and brand landing pages.
- One H1, unique titles/descriptions, consistent canonical URLs, breadcrumb and Product metadata.
- No fabricated aggregate ratings or inferred testimonial stars; no $0 offers for missing prices.
- Preview Product schema deliberately omits offers because the imported inventory is old. Production offers are only emitted for public prices and active/non-pending records.
- Ordinary HTML directory pagination links every inventory listing and customer story.
- The preview allows crawling so search engines can read the noindex directives, and does not advertise its sitemap in robots.txt.
- The production builder refuses an inventory snapshot more than two days old. This is an operational gate, not a guarantee of feed accuracy.

## Before moving MHSRV.com

1. Export existing production URLs from the site, sitemaps and Search Console. Include inventory, brand/type pages, blog/resource pages, images and historical review URLs.
2. Preserve high-value category paths where possible: `/diesel-pusher-rvs`, `/new-rvs-for-sale`, `/entegra-rv` and other established destinations. Verify trailing slash behavior on the production server.
3. Build a complete old-to-new URL map. `redirects-301.csv` contains the earlier review-domain map only; it does not cover the entire production site.
4. Use server-side permanent redirects only to the best equivalent page. Do not send every sold RV or missing resource to the homepage. Keep redirects at least a year and longer where useful.
5. Choose `https://mhsrv.com` as the consistent production origin, matching the current www-to-non-www redirect. Update `site-config.json` deliberately; verify every canonical, internal link and sitemap.
6. Connect the live feed, identify the sales/availability source of truth, and define sold-unit retention rules. Do not mark pending or unavailable inventory InStock.
7. Review legal notices, financing disclosures, contact numbers and model-year resource labels with the business before launch.
8. Keep internal searches, saved lists and comparison URLs out of indexing. Add server/robots rules for arbitrary faceted query combinations; do not generate thousands of thin filter landing pages.
9. Configure Search Console, submit the production sitemap, test redirects/canonicals, and check real-device performance before a staged cutover.

## Content and AI discovery

Useful answers need verifiable source content: actual model-year specs, stock-specific options, floorplans, source-labeled brochures, accessible video descriptions/transcripts where available, and honest answers to buyer questions. A model-year brochure does not establish a particular unit’s installed equipment. Historical dealership testimonials are not automatically reviews of current units.

Keep the established brand's 13-year leadership claim tied to its stated scope: American-built motorhomes sold at one location, per Statistical Surveys. Do not expand it into unsupported claims about every RV category or location.

There is no special schema or text file that guarantees visibility in AI answers. Normal crawlability, helpful content and technical SEO remain the foundation.

## Measurement

Track organic qualified leads, inquiry delivery, calls, appointments, stock-page engagement, search zero-result rates and saved/compared RV use. Review performance by channel, landing page and mobile device. Field Core Web Vitals and real lead outcomes should determine subsequent improvements. Event hooks exist in the site, but external analytics/CRM accounts must be connected.

## Official references

- [Site moves with URL changes](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)
- [Ecommerce URL design](https://developers.google.com/search/docs/specialty/ecommerce/designing-a-url-structure-for-ecommerce-sites)
- [Product structured data](https://developers.google.com/search/docs/appearance/structured-data/product)
- [Product snippets](https://developers.google.com/search/docs/appearance/structured-data/product-snippet)
- [Faceted navigation](https://developers.google.com/search/blog/2024/12/crawling-december-faceted-nav)
- [Self-serving review snippets](https://developers.google.com/search/blog/2019/09/making-review-rich-results-more-helpful)
- [AI features and your website](https://developers.google.com/search/docs/appearance/ai-features)
- [Sitemap lastmod and retired ping endpoint](https://developers.google.com/search/blog/2023/06/sitemaps-lastmod-ping)
- [Retirement of Vehicle Listing rich results](https://developers.google.com/search/blog/2025/06/simplifying-search-results)
