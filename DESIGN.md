---
name: Ask the agent
description: A local chat panel for a course agent, set in calm pastel morning light on translucent paper.
colors:
  dawn-top: "#f6e8ee"
  dawn-middle: "#eee9f2"
  dawn-bottom: "#e4ecf5"
  paper: "rgb(255 255 255 / .78)"
  paper-solid: "#fdfcfd"
  hinoki: "#dccab0"
  hinoki-deep: "#a88d68"
  ink: "#2f2a38"
  ink-soft: "#57506a"
  ink-faint: "#6e6882"
  matcha: "#d4e6c9"
  matcha-ink: "#46703b"
  sora: "#d5e5f4"
  sora-ink: "#375f86"
  fuji: "#e4daf2"
  fuji-ink: "#634d99"
  kaki: "#f7dccb"
  kaki-ink: "#9b4a25"
  sakura: "#f8d9e1"
  sakura-ink: "#a3445f"
  sakura-ink-deep: "#8f3651"
  disabled: "#c9bfcf"
  white: "#ffffff"
typography:
  display:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, serif"
    fontSize: "clamp(2rem, 5vw, 2.8rem)"
    fontWeight: 700
    lineHeight: 1.15
  figure:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, serif"
    fontSize: "2.5rem"
    fontWeight: 700
    lineHeight: 1
  headline:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, serif"
    fontSize: "1.55rem"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "0.01em"
  title:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, serif"
    fontSize: "1.3rem"
    fontWeight: 700
    lineHeight: 1.2
  title-small:
    fontFamily: "Shippori Mincho, Hiragino Mincho ProN, serif"
    fontSize: "1.1rem"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "Zen Maru Gothic, Hiragino Maru Gothic ProN, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.7
  body-question:
    fontFamily: "Zen Maru Gothic, Hiragino Maru Gothic ProN, system-ui, sans-serif"
    fontSize: "1.08rem"
    fontWeight: 500
    lineHeight: 1.6
  label:
    fontFamily: "Zen Maru Gothic, Hiragino Maru Gothic ProN, system-ui, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 700
    lineHeight: 1.3
  chip:
    fontFamily: "Zen Maru Gothic, Hiragino Maru Gothic ProN, system-ui, sans-serif"
    fontSize: "0.82rem"
    fontWeight: 500
    lineHeight: 1
  data:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: "0.8rem"
    fontWeight: 400
    lineHeight: 1.9
rounded:
  seal: "2px"
  paper: "3px"
  pill: "99px"
spacing:
  card-inner: "10px"
  panel-gap: "14px"
  gutter: "16px"
  turn: "18px"
  thread: "44px"
components:
  button-primary:
    backgroundColor: "{colors.sakura-ink}"
    textColor: "{colors.white}"
    typography: "{typography.body}"
    rounded: "{rounded.paper}"
    padding: "0 22px"
    height: "52px"
  button-primary-hover:
    backgroundColor: "{colors.sakura-ink-deep}"
    textColor: "{colors.white}"
  button-primary-disabled:
    backgroundColor: "{colors.disabled}"
    textColor: "{colors.white}"
  sample-card:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.paper}"
    padding: "16px 18px"
  sample-card-hover:
    backgroundColor: "{colors.paper-solid}"
  panel:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.paper}"
    padding: "18px 20px"
  panel-answer:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.paper}"
    padding: "34px 20px 18px"
  chip:
    backgroundColor: "{colors.paper-solid}"
    textColor: "{colors.ink-soft}"
    typography: "{typography.chip}"
    rounded: "{rounded.paper}"
    padding: "6px 11px"
  tag:
    backgroundColor: "{colors.sora}"
    textColor: "{colors.sora-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.paper}"
    padding: "6px 10px"
  input:
    backgroundColor: "{colors.paper-solid}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.paper}"
    padding: "13px 16px"
    height: "52px"
  seal-answered:
    backgroundColor: "{colors.matcha}"
    textColor: "{colors.matcha-ink}"
    rounded: "{rounded.seal}"
    size: "42px"
  seal-no-data:
    backgroundColor: "{colors.sora}"
    textColor: "{colors.sora-ink}"
    rounded: "{rounded.seal}"
    size: "42px"
  seal-step-limit:
    backgroundColor: "{colors.fuji}"
    textColor: "{colors.fuji-ink}"
    rounded: "{rounded.seal}"
    size: "42px"
  seal-failed:
    backgroundColor: "{colors.kaki}"
    textColor: "{colors.kaki-ink}"
    rounded: "{rounded.seal}"
    size: "42px"
  seal-working:
    backgroundColor: "{colors.sakura}"
    textColor: "{colors.sakura-ink}"
    rounded: "{rounded.seal}"
    size: "42px"
  seal-question:
    backgroundColor: "{colors.sakura}"
    textColor: "{colors.sakura-ink}"
    rounded: "{rounded.seal}"
    size: "32px"
---

# Design System: Ask the agent

## Overview

**Creative North Star: "Shoji Morning"**

The page is a quiet room at dawn. A fixed vertical wash runs from a pink haze at the top to a pale sky blue at the bottom, and everything readable sits on white paper that lets a little of that light through. A thin warm-wood line frames each sheet. Every outcome gets one square seal in its own pastel. The seal and one short line say how the run ended, so nothing else on the page needs to shout.

The pages are sparse and unhurried. There is one centred column, generous gaps between turns, and a reading line of about 68 characters. Ornament is limited to three devices that the world uses on purpose: the seal, the lattice rail across the top of an answer, and the dawn wash. Motion has one authored moment, the seal pressing in and the paper sliding open from the centre. The only other movement is the slow breathing of the working seal.

The seals carry drawn line marks (a check, a ruled circle, a bar with an arrow, a cross, sliders, an hourglass, a question mark), not lettering. The world carries no Japanese words or characters. That is a user decision.

**Key Characteristics:**
- A fixed dawn gradient as the ground, with translucent white paper laid on it
- Thin warm-wood borders instead of shadows
- One pastel fill and a matching ink per outcome, shown through a square seal
- A Mincho serif for titles, a rounded gothic for reading, and monospace only for machine values
- One slide-open reveal per answer and nothing louder

## Colors

A pastel palette at dawn. Each hue appears in two strengths: a soft fill for surfaces and a deep ink for marks and text.

### Primary
- **Sakura Ink** (sakura-ink): The single action colour. It fills the Ask button and is the caret colour, and it inks the question seal and the working seal. On hover the button darkens to **Deep Sakura** (sakura-ink-deep).
- **Sakura Haze** (sakura): The fill of the question seal and the working seal, and the text selection colour.

### Secondary (outcome pairs)
- **Matcha** (matcha / matcha-ink): Answered. Its ink also fills finished step cells and the token budget bar at rest.
- **Sora** (sora / sora-ink): No data or partly in the records. Its ink also serves links, the focus ring, the rain bar and the umbrella tag. Gap cards tint toward it with a dashed border.
- **Fuji** (fuji / fuji-ink): The step limit was reached.
- **Kaki** (kaki / kaki-ink): Failure (connection, setup, server offline). Its ink also marks failed steps, error text and a full token budget.

### Neutral
- **Dawn Haze to Pale Sora** (dawn-top, dawn-middle, dawn-bottom): The three stops of the fixed page gradient (0%, 45%, 100%).
- **Shoji Paper** (paper): Translucent white for panels and sample cards. The header and composer use the same white at lower opacity (.55 and .6), and the step trail uses .5.
- **Solid Paper** (paper-solid): Opaque white for the input, the chips and hovered sample cards.
- **Hinoki** (hinoki): Every frame line, divider and the scrollbar thumb. Table rules use it at 70% alpha, and code backgrounds use it at 30%.
- **Deep Hinoki** (hinoki-deep): Hover borders, the lattice rail's lower edge, card icon strokes and the input focus border.
- **Sumi Plum** (ink), **Soft Plum** (ink-soft), **Faint Plum** (ink-faint): Text at three strengths. Faint is the floor and is used for timestamps, step numbers, ms values, placeholders and the hint line.

### Named Rules
**The Two Strengths Rule.** Every hue comes as a pastel fill plus a deep ink. Large surfaces only ever take the pastel or paper. Ink-strength fills are allowed only at small scale: the Ask button, progress bars, step cells and tags.

**The Outcome Owns Its Colour Rule.** Matcha, sora, fuji, kaki and sakura each mean one outcome. A new surface may reuse a pair only for that same meaning.

## Typography

**Display Font:** Shippori Mincho (with Hiragino Mincho ProN, serif)
**Body Font:** Zen Maru Gothic (with Hiragino Maru Gothic ProN, system-ui, sans-serif)
**Label/Mono Font:** JetBrains Mono (with ui-monospace, monospace)

**Character:** The calligraphic Mincho serif gives each heading the weight of a printed title. The rounded gothic keeps long reading soft and friendly. The monospace stays a tool for numbers and code and never carries the voice. All three fonts are self-hosted as woff2.

### Hierarchy
- **Display** (700, clamp 2rem to 2.8rem, 1.15): The empty-state greeting only.
- **Figure** (700, 2.5rem, 1): A single headline number on a data card (temperature).
- **Headline** (700, 1.55rem, 1.1, +0.01em): The page title in the header. It drops to 1.25rem under 600px.
- **Title** (700, 1.3rem, 1.2): The outcome name next to its seal, set in the outcome's ink.
- **Title small** (700, 1.1rem, 1.3): Data card headings.
- **Body** (400, 16px, 1.7): All reading text. Answer paragraphs are capped at 68ch.
- **Body question** (500, 1.08rem, 1.6): The user's question at the head of a turn.
- **Label** (700, 0.78rem, 1.3): Table headers and tags. Sentence case, no tracking.
- **Data** (400 to 600, 0.78 to 0.9rem): Times, dates, ms, step numbers, arguments, prices and token counts.

### Named Rules
**The Machine Values Rule.** JetBrains Mono is used only for values a machine produced: times, dates, durations, counts, prices and tool arguments. Names, prose and labels stay in the gothic, including train names and "direct / 2 changes" in a monospace table.

**The No Uppercase Rule.** No text in the system is uppercased or letter-spaced for emphasis. Hierarchy comes from the serif and its weight.

## Layout

The page is a three-row grid: header, a scrolling thread, and a pinned composer. The thread and the composer form share one centred column (820px max, 16px side padding). The header spans the full width, with padding of clamp(16px, 4vw, 40px). The title sits at the left and the meta cluster (token budget, model chip, step-limit chip) at the right, and the header wraps when space runs out.

Rhythm runs from loose to tight as you move inward: 44px between turns, 18px within a turn, 16px between an outcome and its screen, 14px between panels and data cards, and 10px inside a card. Data cards sit in a two-column grid. An odd small card spans the full row, and tables always span the full row and come last. Sample questions use the same two-column grid at 700px max.

Below 600px, the cards and samples drop to one column and the chips and the hint line are hidden. The budget takes the full header width, the step trail drops its ms column under the step text, and the Ask button keeps only its arrow. The composer respects the bottom safe-area inset.

## Elevation & Depth

The system is flat. Depth comes from the translucency of the paper over the dawn gradient and from thin hinoki borders, not from shadows. There are three exceptions, each tied to a specific job.

### Shadow Vocabulary
- **Action lift** (`box-shadow: 0 2px 6px rgb(47 42 56 / .18)`): Only on the Ask button, so the single action reads as pressable. It is removed when the button is disabled.
- **Focus wash** (`box-shadow: 0 0 0 3px rgb(168 141 104 / .2)`): The textarea's focus halo in hinoki.
- **Seal double rule** (`box-shadow: inset 0 0 0 2px <fill>, inset 0 0 0 3px <ink at 55%>`): The inner second frame line of an outcome seal. The smaller question seal leaves it out.

### Named Rules
**The Paper Not Plastic Rule.** Surfaces separate by border and translucency. A new panel gets a 1px hinoki line, never a drop shadow.

## Shapes

Corners are nearly square. Paper surfaces (panels, cards, the trail, chips, tags, the input, the button) all use 3px. Seals are tighter at 2px so they read as stamped blocks. Fully rounded ends appear only on the thin 7px progress tracks (the token budget and rain probability). Frames are 1px hinoki lines. The one exception is the gap card, which uses a dashed border tinted toward sora to show missing data. The lattice rail is a 16px band of a fine kumiko-style grid drawn in light hinoki, with a deep hinoki line along its lower edge. It runs only along the top of an answer panel.

## Components

### Buttons
Calm and solid: there is one coloured button, and it is the only one.
- **Shape:** Nearly square corners (3px), 52px tall to match the input.
- **Primary:** Sakura ink fill, white bold text (700, 1rem), a drawn arrow icon at 18px and 22px horizontal padding.
- **Hover / Focus:** It deepens to Deep Sakura and lifts 1px (0.2s). Focus uses the global 2px sora-ink outline with a 3px offset.
- **Disabled:** A lilac-grey fill and a progress cursor while a run is in flight. The lift and the shadow are removed.
- **Sample cards (secondary):** Question cards in the empty state. They are paper with a hinoki border (16px 18px padding, 500 weight). On hover they turn solid, the border deepens to deep hinoki and the card rises 2px (0.3s).

### Chips
- **Style:** Solid paper with a 1px hinoki border, soft ink text (500, .82rem) and the value in bold ink. They show the model and the step limit, and context facts on a card, where the value is monospace.
- **Tags:** A sora fill with sora ink, a bold label and no border. They carry a single advisory on a data card ("Take an umbrella").

### Cards / Containers
- **Corner Style:** 3px.
- **Background:** Shoji paper (translucent white).
- **Shadow Strategy:** None (see Elevation & Depth).
- **Border:** 1px hinoki. Gap cards use a dashed border mixed toward sora on a faint sora wash.
- **Internal Padding:** 18px 20px. The answer panel takes 34px at the top to clear the lattice rail.
- **Card head:** A 20px drawn line icon stroked in deep hinoki, a Mincho title, and a monospace date pushed to the right in faint ink.

### Inputs / Fields
- **Style:** A solid paper textarea with a 1px hinoki border and 3px corners. It is 52px tall at minimum, grows up to 180px, and has a faint placeholder.
- **Focus:** The border deepens to deep hinoki and the hinoki focus wash appears. There is no outline.

### Navigation
There is no navigation. The header holds only the title and the run meta. The token budget is a small labelled bar: matcha ink at rest and kaki ink when full, with a soft note under it.

### Seal (signature)
A square stamp with a 2px ink frame, a pastel fill and an inner second rule. It holds one drawn line mark (24px, in currentColor) and appears at 42px beside the outcome name. Its colour pair is set by the reply's outcome, so the seal, the title and the final step cell all share one ink. The question seal is 32px in sakura with a single 1.5px frame. While the agent works, the sakura seal breathes (scale .92, opacity .6, 2.4s ease-in-out, infinite).

### Step Trail (signature)
A collapsed disclosure on semi-transparent paper. The summary shows counts (steps, tool calls, failures, tokens). Each step is one row: a 12px square status cell, the step number in monospace, the tool and its arguments, and the ms value. A finished cell is a solid matcha-ink square. A failed cell is a hollow kaki square with a diagonal strike and the reason in kaki below. The final step takes the outcome's seal ink.

### Motion
The reveal runs once per answer. The seal presses in (scale 1.12 to 1, 0.6s expo-out). The outcome text eases in from 8px to the left. Then the screen opens from the centre (clip-path inset 50% to 0, 0.9s power3 in-out). Progress bars ease on cubic-bezier(.22, 1, .36, 1) over 0.8s. All animation and transitions turn off under prefers-reduced-motion.

## Do's and Don'ts

### Do:
- **Do** put every reading surface on Shoji Paper with a 1px hinoki border and 3px corners.
- **Do** give each run outcome its seal, its name in the outcome ink, and one short plain line.
- **Do** keep JetBrains Mono for machine values only (times, durations, counts, prices, arguments).
- **Do** keep reading text at 16px / 1.7 in Zen Maru Gothic, with prose capped at 68ch.
- **Do** keep the 2px sora-ink focus outline with a 3px offset on every interactive element.
- **Do** honour prefers-reduced-motion by turning off the breathing and the slide-open reveal.

### Don't:
- **Don't** put Japanese words or kanji in seals or anywhere else in the interface; seals carry drawn line marks.
- **Don't** use sun-ray or radiating-sun motifs, or any symbol tied to militarism or nationalism.
- **Don't** use drop shadows on panels or cards; only the Ask button carries a lift shadow.
- **Don't** fill a large surface with an ink-strength colour; the Ask button is the only sizeable ink fill.
- **Don't** reuse an outcome colour pair for a different meaning.
- **Don't** add a second lattice rail or a second authored animation; the lattice belongs to the answer panel and the reveal belongs to the answer.
