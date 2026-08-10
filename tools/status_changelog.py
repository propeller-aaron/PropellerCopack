"""Hand-maintained changelog of notable fixes shown on the status dashboard.

Newest entries first. This is a durable record — unlike the audit-generated
sections, it is NOT recomputed from a live crawl, so entries persist across
regenerations of status/index.html.
"""

CHANGELOG_ENTRIES = [
    {
        "date": "2026-08-10",
        "title": "Fixed Google Search Console indexing issues",
        "detail": (
            "Aaron shared a Google Search Console coverage export "
            "(propellercopack.com-Coverage-2026-08-10.xlsx) flagging two critical "
            "issues: 1 page with a redirect and 1 page “Crawled – currently not "
            "indexed.” Root cause: kitting-and-assembly/ was cloned from "
            "custom-projects/ and its meta description, og:title/description, and "
            "twitter:title/description tags were never updated, so Google treated it "
            "as duplicate content of an already-indexed page. It was also missing "
            "from sitemap.xml despite being linked from the homepage, so Google only "
            "discovered it through inconsistent URL forms. Fixed by giving the page "
            "unique meta/social tags and adding it to sitemap.xml with its own hero "
            "image entries. The http/www/non-trailing-slash redirects Google also "
            "reported were checked and confirmed to be correct canonicalization, not "
            "bugs — no action needed there."
        ),
    },
]
