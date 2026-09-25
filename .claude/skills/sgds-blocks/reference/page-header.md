# Page Header

A page-level header block with an overline label, heading, and supporting
description — optionally preceded by a breadcrumb trail. Use at the top
of any content page to orient the user. **Confirmed against both actual
upstream source files below: neither includes an icon or a CTA button**
— if a page needs those, compose them separately (e.g. an icon next to
the heading, or a button in the same row) rather than expecting this
block to provide them.

## When to use

- Any page that benefits from a breadcrumb trail for navigation context
- Any content page that needs a consistent overline/heading/description
  header treatment

## Block anatomy

```
Page header
├── Breadcrumb (sgds-breadcrumb) — optional, only in the breadcrumb variant
└── Heading group
    ├── Overline label (text-overline-md, uppercase)
    ├── h1 heading (text-heading-xl)
    └── Description paragraph (text-body-lg)
```

## Source files

**Base URL:** `https://raw.githubusercontent.com/GovTechSG/sgds-web-component/master/stories/blocks/header/`

| Block Name | File Path | URL |
|---|---|---|
| Page Header (no breadcrumb) | `page-header.stories.js` | [page-header.stories.js](https://raw.githubusercontent.com/GovTechSG/sgds-web-component/master/stories/blocks/header/page-header.stories.js) |
| Page Header with Breadcrumb | `page-header-breadcrumb.stories.js` | [page-header-breadcrumb.stories.js](https://raw.githubusercontent.com/GovTechSG/sgds-web-component/master/stories/blocks/header/page-header-breadcrumb.stories.js) |

## Complete block (breadcrumb variant)

```html
<section class="sgds:bg-default sgds:py-layout-lg">
  <div class="sgds-container">
    <sgds-breadcrumb>
      <sgds-breadcrumb-item href="/">Home</sgds-breadcrumb-item>
      <sgds-breadcrumb-item href="/section">Section</sgds-breadcrumb-item>
      <sgds-breadcrumb-item active>Current Page</sgds-breadcrumb-item>
    </sgds-breadcrumb>
    <div class="sgds:text-overline-md sgds:font-semibold sgds:leading-2-xs sgds:tracking-wide sgds:uppercase sgds:text-label-default sgds:mb-xs">
      Overline Label
    </div>
    <h1 class="sgds:text-heading-xl sgds:font-bold sgds:leading-xl sgds:tracking-tight sgds:text-heading-default">
      Page Heading Goes Here
    </h1>
    <p class="sgds:text-body-lg sgds:leading-md sgds:tracking-normal sgds:text-body-subtle">
      Supporting body text that provides context and detail about this page.
    </p>
  </div>
</section>
```

## Customisation notes

- Breadcrumb depth: add or remove `<sgds-breadcrumb-item>` elements; always mark the current page with `active`
- Omit the `<sgds-breadcrumb>` element entirely for the no-breadcrumb variant
- If the page needs an icon or a primary action button, add them yourself alongside the heading — they are not part of either upstream variant of this block
