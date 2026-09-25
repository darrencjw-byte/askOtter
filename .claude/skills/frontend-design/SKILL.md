---
name: "frontend-design"
description: "Design methodology for grounding aesthetic decisions in the app's actual subject matter instead of defaulting to generic template looks. Applies to: sgds-theming's brand colour/night-mode/font choice, how sgds-blocks are composed on a page, and — whenever SGDS has no equivalent component at all (per CLAUDE.md's Component Priority table) — palette/typography/layout for a shadcn/ui component, a user-approved third-party library, or pure custom Tailwind/React. Never applies to overriding an `<sgds-*>` component's own internal styling. Operates within design-system.md's existing gov-appropriate register — not a license for bold or maximalist design. Adapted from Anthropic's official frontend-design skill (Apache License 2.0) — see LICENSE.txt in this folder."
metadata:
  author: viber-studio
  version: "1.0.0"
  audience: internal
  category: pattern
  source: "Adapted from https://github.com/anthropics/skills/tree/main/skills/frontend-design (Apache License 2.0, full text in LICENSE.txt alongside this file). Modified: added the 'Scope inside this template' section below, anchoring the methodology to whatever fills the gap once SGDS doesn't cover a need (shadcn, an approved third-party library, or custom code) and this template's gov-appropriate register — that section is not present in the original."
---

# Frontend Design

> Adapted from Anthropic's official `frontend-design` skill (Apache License
> 2.0 — full text in `LICENSE.txt` next to this file). The "Scope inside
> this template" section immediately below is new; everything after it is
> the original methodology.

## Scope inside this template — read this first

This skill's *specific mechanics* — freely choosing 4–6 hex values,
freely pairing 2+ typefaces — do not apply to how `<sgds-*>` components
render their own internals. Never use this methodology to justify skipping
an available SGDS component, or overriding its internal styling with
arbitrary CSS: SGDS's own semantic tokens are the actual visual language
for every `<sgds-*>` element, not a starting point to improve on. SGDS
remains the mandatory default (CLAUDE.md's Component Priority table).

That said, SGDS is not fully closed off from this skill either — it has
its own sanctioned, narrower customisation surface, and a real
composition decision above the component level:

- **[sgds-theming](../sgds-theming/SKILL.md)'s brand colour, night mode,
  and font override.** Grounding *that* choice in the app's actual
  subject — instead of defaulting to SGDS's own out-of-the-box purple +
  Inter — is exactly the judgment this skill is for. Apply it strictly
  within sgds-theming's own mechanism: never override individual semantic
  tokens directly, never mix multiple GT palettes, never invent a hex
  value for a GovTech product outside the approved `themes/gt/` set.
- **How SGDS blocks are composed on a page** — which `sgds-blocks`
  pattern, in what order, what content leads. SGDS supplies the building
  blocks; it doesn't dictate this specific app's narrative or which
  combination suits its subject. Ground that composition decision here
  too, even when every element used is 100% SGDS.

Beyond theming and composition, use this skill in full once you've
confirmed SGDS has no equivalent component at all, and a real design
decision is on the table — palette, typography, or layout for whatever
fills that gap. What actually fills it doesn't change whether this skill
applies: a shadcn/ui component (`vibe-shadcn`), a user-approved
third-party library (`vibe-npm`, after the confirm-before-proceeding
warning), or pure custom Tailwind/React with no component library at all.
The trigger is "a genuine design decision exists," not "shadcn
specifically got used."

Inside that zone, this methodology operates **within**
[design-system.md](../design-system.md)'s existing register, not instead
of it:

- "Take one real aesthetic risk" still means clean, engineered, calm — not
  playful (design-system.md's Interior Design Principles). The signature
  element below is the one place that risk shows up; everything else stays
  inside the restrained palette, spacing, and status-colour rules already
  defined there.
- Accessibility, keyboard focus, and reduced-motion support are
  non-negotiable regardless of how bold the direction is — this matches
  the original's own "quality floor" requirement (see "Restraint and
  self-critique" below).
- If a page falls under design-system.md's "Style Selection by Context"
  table (dashboard, form-focused, dense table, etc.), that table's
  treatment is the floor — this skill sharpens execution within it, it
  does not override the category.

---

Approach this as the design lead at a small studio known for giving every client a visual identity that could not be mistaken for anyone else's. This client has already rejected proposals that felt templated, and is paying for a distinctive point of view: make deliberate, opinionated choices about palette, typography, and layout that are specific to this brief, and take one real aesthetic risk you can justify.

## Ground it in the subject

If the brief does not pin down what the product or subject is, pin it yourself before designing: name one concrete subject, its audience, and the page's single job, and state your choice. If there's any information in your memory about the human's preferences, context about what they're building, or designs you've made before – use that as a hint. The subject's own world, its materials, instruments, artifacts, and vernacular, is where distinctive choices come from. Build with the brief's real content and subject matter throughout.

## Design principles

For web designs, the hero is a thesis. Open with the most characteristic thing in the subject's world, in whatever form makes sense for it: a headline, an image, an animation, a live demo, an interactive moment. Be deliberate with your choice: a big number with a small label, supporting stats, and a gradient accent is the template answer, only use if that's truly the best option.

Typography carries the personality of the page. Pair the display and body faces deliberately, not the same families you would reach for on any other project, and set a clear type scale with intentional weights, widths, and spacing. Make the type treatment itself a memorable part of the design, not a neutral delivery vehicle for the content.

Structure is information. Structural devices, numbering, eyebrows, dividers, labels, should encode something true about the content, not decorate it. Many generic designs use numbered markers (01 / 02 / 03), but that's only appropriate if the content actually is a sequence - like a real process or a typed timeline where order carries information the reader needs. Question if choices like numbered markers actually make sense before incorporating them.

Leverage motion deliberately. Think about where and if animation can serve the subject: a page-load sequence, a scroll-triggered reveal, hover micro-interactions, ambient atmosphere. An orchestrated moment usually lands harder than scattered effects; choose what the direction calls for. However, sometimes less is more, and extra animation contributes to the feeling that the design is AI-generated.

Match complexity to the vision. Maximalist directions need elaborate execution; minimal directions need precision in spacing, type, and detail. Elegance is executing the chosen vision well.

Consider written content carefully. Often a design brief may not contain real content, and it's up to you to come up with copy. Copy can make a design feel as templated as the design itself. See the below section on writing for more guidance.

## Process: brainstorm, explore, plan, critique, build, critique again

For calibration: AI-generated design right now clusters around three looks: (1) a warm cream background (near #F4F1EA) with a high-contrast serif display and a terracotta accent; (2) a near-black background with a single bright acid-green or vermilion accent; (3) a broadsheet-style layout with hairline rules, zero border-radius, and dense newspaper-like columns. All three are legitimate for some briefs, but they are defaults rather than choices, and they appear regardless of subject. Where the brief pins down a visual direction, follow it exactly — the brief's own words always win, including when it asks for one of these looks. Where it leaves an axis free, don't spend that freedom on one of these defaults. Just like a human designer who's hired, there's often a careful balance between doing what you're good at and taking each project as a chance to experiment and learn.

Work in two passes. First, brainstorm a short design plan based on the human's design brief: create a compact token system with color, type, layout, and signature. Color: describe the palette as 4–6 named hex values. Type: the typefaces for 2+ roles (a characterful display face that's used with restraint, a complementary body face, and a utility face for captions or data if needed). Layout: a layout concept, using one-sentence prose descriptions and ASCII wireframes to ideate and compare. Signature: the single unique element this page will be remembered by that embodies the brief in an appropriate way.

Then review that plan against the brief before building: if any part of it reads like the generic default you would produce for any similar page (work through a similar prompt to see if you arrive somewhere similar) rather than a choice made for this specific brief — revise that part, say what you changed and why. Only after you've confirmed the relative uniqueness of your design plan should you start to write the code, following the revised plan exactly and deriving every color and type decision from it.

When writing the code, be careful of structuring your CSS selector specificities. It's easy to generate CSS classes that cancel each other out (especially with a type-based selector like .section and a element-based selector like .cta). This can happen often with paddings/margins between sections.

Try to do a lot of this planning and iteration in your thinking, and only show ideas to the user when you have higher confidence it'll delight them.

## Restraint and self-critique

Spend your boldness in one place. Let the signature element be the one memorable thing, keep everything around it quiet and disciplined, and cut any decoration that does not serve the brief. Not taking a risk can be a risk itself! Build to a quality floor without announcing it: responsive down to mobile, visible keyboard focus, reduced motion respected. Critique your own work as you build, taking screenshots if your environment supports it – a picture is worth 1000 tokens. Consider Chanel's advice: before leaving the house, take a look in the mirror and remove one accessory. Human creators have memory and always try to do something new, so if you have a space to quickly jot down notes about what you've tried, it can help you in future passes.

## More on writing in design

Words appear in a design for one reason: to make it easier to understand, and therefore easier to use. They are design material, not decoration. Bring the same intentionality to copy that you would bring to spacing and color. Before writing anything, ask what the design needs to say, and how it can best be said to help the person navigate the experience.

Write from the end user's side of the screen. Name things by what people control and recognize, never by how the system is built. A person manages notifications, not webhook config. Describe what something does in plain terms rather than selling it. Being specific is always better than being clever.

Use active voice as default. A control should say exactly what happens when it's used: "Save changes," not "Submit." An action keeps the same name through the whole flow, so the button that says "Publish" produces a toast that says "Published." The vocabulary of an interface is the signposting for someone navigating the product. Cohesion and consistency are how people learn their way around.

Treat failure and emptiness as moments for direction, not mood. Explain what went wrong and how to fix it, in the interface's voice rather than a person's. Errors don't apologize, and they are never vague about what happened. An empty screen is an invitation to act.

Keep the register conversational and tuned: plain verbs, sentence case, no filler, with tone matched to the brand and the audience. Let each element do exactly one job. A label labels, an example demonstrates, and nothing quietly does double duty.

---
*Prepared by CIOO Rabbit Team, adapted from Anthropic's `frontend-design`
skill (Apache License 2.0) · For use with VIBER Studio on Rabbit Deploy*
