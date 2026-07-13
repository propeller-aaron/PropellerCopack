# Website content (Word documents)

Edit site copy in Microsoft Word. Each `.docx` file maps to page sections on the live site.

## Folders

| Folder | Purpose |
|--------|---------|
| `content/pages/` | One document per page (`homepage.docx` + one per service URL) |
| `content/shared/` | Copy that appears on multiple pages (banner, contact, footer) |

## Workflow

1. **Export** (refresh Word files from the current website):
   ```bash
   pip install -r requirements.txt
   python tools/export_content_docs.py
   ```

2. **Edit** the `.docx` files in Word. Change the text under each section heading.
   - Do **not** delete or rename the `[[block:...]]` marker lines.
   - Press **Enter** for line breaks (they become `<br>` on the site).
   - Link URLs and images are not changed from Word—only text fields.

3. **Apply** (push your Word edits to the HTML pages):
   ```bash
   python tools/apply_content_docs.py
   ```

4. Deploy/sync the updated HTML files to your web server.

## What is editable

**Per service page** (`content/pages/{slug}.docx`):
- Browser title and SEO description
- Page hero title (H1)
- Page body paragraph
- Hero image alt text

**Homepage** (`content/pages/homepage.docx`):
- Hero title, subtitle, and paragraph
- Feature cards (titles + image alt text)
- Packaging section (title + card labels)
- Service link labels (URLs stay the same)
- Homepage contact intro text

**Shared documents** (`content/shared/`):
- `inner-banner.docx` — top banner on all 23 service pages
- `contact-inner.docx` — “Drop us a line” section on service pages
- `footer.docx` — office, manufacturing, and contact footer on all pages

**Not editable here:** navigation chrome, HubSpot contact form, images/files, page URLs.
