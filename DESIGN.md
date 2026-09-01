---
name: Sonic Ledger
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#cbc3d7'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#958ea0'
  outline-variant: '#494454'
  surface-tint: '#d0bcff'
  primary: '#d0bcff'
  on-primary: '#3c0091'
  primary-container: '#a078ff'
  on-primary-container: '#340080'
  inverse-primary: '#6d3bd7'
  secondary: '#4edea3'
  on-secondary: '#003824'
  secondary-container: '#00a572'
  on-secondary-container: '#00311f'
  tertiary: '#ffb869'
  on-tertiary: '#482900'
  tertiary-container: '#ca801e'
  on-tertiary-container: '#3f2300'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e9ddff'
  primary-fixed-dim: '#d0bcff'
  on-primary-fixed: '#23005c'
  on-primary-fixed-variant: '#5516be'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdcbb'
  tertiary-fixed-dim: '#ffb869'
  on-tertiary-fixed: '#2c1700'
  on-tertiary-fixed-variant: '#673d00'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  title-lg:
    fontFamily: Geist
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
  title-md:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '500'
    lineHeight: 24px
  body-lg:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  metadata:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 14px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: Geist
    fontSize: 10px
    fontWeight: '700'
    lineHeight: 12px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  sidebar-width: 260px
  inspector-width: 320px
  gutter: 20px
---

## Brand & Style

The design system is engineered for professional music librarians and power users who require precision and focus. The brand personality is technical, sophisticated, and utilitarian, prioritizing information density without sacrificing aesthetic clarity. 

The visual style is a refined **Minimalism** with a **Technical** edge. It utilizes a deep dark-mode palette to reduce eye strain during long sessions of metadata tagging. Depth is achieved through "Tonal Elevation"—layering slightly lighter slate grays upon a charcoal base—rather than heavy shadows. This creates a focused environment where album artwork and colorful tags provide the primary visual interest.

## Colors

This design system uses a strict dark-mode hierarchy to manage visual noise.

- **Backgrounds**: The base layer uses Deep Charcoal (#121212).
- **Surfaces**: Primary surfaces (sidebars, main content areas) use Slate Gray (#1E1E1E). Secondary surfaces (cards, popovers, active states) use a lighter Slate Gray (#2A2A2A).
- **Accents**: Electric Violet (#8B5CF6) is used for primary actions, focus states, and progress indicators. Emerald (#10B981) serves as a secondary accent for success states or specific metadata highlights (e.g., "Verified" tags).
- **Typography**: Text uses a high-contrast off-white for primary readability and a muted blue-gray for secondary metadata.

## Typography

The typography system relies on **Geist** for its systematic, developer-friendly aesthetic that excels in high-density interfaces. 

- **Data Presentation**: For technical metadata like BPM, bitrates, or file sizes, **JetBrains Mono** is introduced to provide clear character distinction and a "data-first" feel.
- **Hierarchy**: Use `display` for main library headers and `metadata` for list-view columns. Use `label-caps` for section headers within the tag editor sidebar to create clear categorical separation.

## Layout & Spacing

The design system utilizes a **Fixed-Sidebar / Fluid-Content** layout model. 

1.  **Sidebar (Left)**: Fixed at 260px. Contains primary navigation and library filters.
2.  **Main Content (Center)**: Fluid grid. Adjusts between Album Art (Grid) and Metadata (List) views.
3.  **Inspector (Right)**: Fixed at 320px. Used for the detailed tag editor.

Spacing follows a strict 4px grid. Use `md` (16px) for standard padding within cards and containers, and `sm` (8px) for related grouping of input fields or metadata tags.

## Elevation & Depth

In this dark-themed system, elevation is conveyed through **Tonal Layering** and **Subtle Outlines** rather than traditional shadows.

- **Level 0 (Background)**: #121212. Used for the application frame.
- **Level 1 (Surface)**: #1E1E1E. Used for the sidebar and main workspace background.
- **Level 2 (In-app Surface)**: #2A2A2A. Used for cards, buttons, and input fields.
- **Borders**: All interactive elements and surfaces should feature a 1px solid border at 10% white opacity (`rgba(255,255,255,0.1)`). This provides definition between dark layers without creating harsh contrast.
- **Focus States**: 1px solid Electric Violet border with a 4px soft glow (`rgba(139, 92, 246, 0.3)`) to indicate active editing or keyboard focus.

## Shapes

The shape language is **Soft** and precise. 

- **Standard Elements**: Buttons, inputs, and album cards use `rounded-sm` (4px) to maintain a professional, architectural feel. 
- **Large Elements**: Dialogs or the tag-editor sidebar container use `rounded-lg` (8px). 
- **Tags/Pills**: Genre tags and multi-select items use a slightly higher `rounded-xl` (12px) to differentiate them from functional buttons.

## Components

### Buttons
- **Primary**: Electric Violet background, white text. No shadow, 1px top-light border.
- **Secondary/Ghost**: Ghost borders (10% white) with #F8FAFC text. On hover, background becomes #2A2A2A.
- **Destructive**: Muted red text with ghost border, turning solid red only on hover.

### List View Rows
- Height: 40px. 
- Border-bottom: 1px solid rgba(255,255,255,0.05).
- Alternate row striping is not used; instead, use a #2A2A2A background on hover across the full width of the row.

### Album Cards (Grid View)
- Aspect Ratio: 1:1 for artwork.
- Transition: Subtle 2px lift or "glow" border on hover.
- Metadata: Title (Primary Text), Artist (Secondary Text, smaller).

### Tag Editor Sidebar
- Inputs: Darker background (#121212), 1px border. Focus state uses primary accent.
- Multi-select: Items appear as small pills with a "close" icon.
- Dropdowns: Use a #2A2A2A surface with a subtle shadow (blur: 12px, opacity: 0.4) to separate from the sidebar surface.

### Sidebar Navigation
- Active state: Left-side 2px vertical bar in Electric Violet. 
- Text: Secondary color, shifting to Primary on active or hover.