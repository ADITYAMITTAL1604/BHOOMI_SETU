---
name: BhoomiSetu
colors:
  surface: '#fcf9f0'
  surface-dim: '#dddad1'
  surface-bright: '#fcf9f0'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3ea'
  surface-container: '#f1eee5'
  surface-container-high: '#ebe8df'
  surface-container-highest: '#e5e2da'
  on-surface: '#1c1c17'
  on-surface-variant: '#41484e'
  inverse-surface: '#31312b'
  inverse-on-surface: '#f4f1e8'
  outline: '#71787f'
  outline-variant: '#c0c7cf'
  surface-tint: '#1e648d'
  primary: '#00557d'
  on-primary: '#ffffff'
  primary-container: '#2b6d97'
  on-primary-container: '#d4eaff'
  inverse-primary: '#91cdfc'
  secondary: '#0d6a61'
  on-secondary: '#ffffff'
  secondary-container: '#a2f1e5'
  on-secondary-container: '#197067'
  tertiary: '#2d5a15'
  on-tertiary: '#ffffff'
  tertiary-container: '#44732b'
  on-tertiary-container: '#c0f79f'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#cae6ff'
  primary-fixed-dim: '#91cdfc'
  on-primary-fixed: '#001e30'
  on-primary-fixed-variant: '#004b70'
  secondary-fixed: '#a2f1e5'
  secondary-fixed-dim: '#87d5c9'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#bbf29b'
  tertiary-fixed-dim: '#a0d581'
  on-tertiary-fixed: '#082100'
  on-tertiary-fixed-variant: '#24510c'
  background: '#fcf9f0'
  on-background: '#1c1c17'
  surface-variant: '#e5e2da'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  title-lg:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  mono-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  container-max: 1440px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 32px
  section-gap: 48px
---

## Brand & Style

The design system is engineered for a high-stakes, national-level command center. It balances the gravity of government-grade data with the efficiency of modern enterprise software. The aesthetic is "Modern Enterprise GIS," characterized by deep, Earth-toned professionalism and high-density information architecture.

The brand personality is authoritative and intelligent. It evokes a sense of "operational control" through precise alignment, rigorous spacing, and a utilitarian interface that stays out of the way of the data. To reinforce its land-based mission, the system incorporates subtle topographical contour line-work as background motifs and parcel-boundary patterns in data visualization. 

**Core Style Characteristics:**
- **Corporate / Modern:** Systematic, reliable, and functional.
- **Data-Rich:** Optimized for large datasets, complex tables, and geographic information systems.
- **Professional Transparency:** Uses clear visual hierarchies to ensure accountability and clarity in land acquisition workflows.

## Colors

The palette, titled "The Harmonious Earth," is grounded in natural tones representing the land, water, and infrastructure involved in national acquisition projects.

- **Primary (Deep Teal Blue):** Used for the primary navigation sidebar, header background, and critical call-to-action buttons. It establishes the "command" presence.
- **Secondary (Muted Sea Green):** Applied to progress bars, secondary actions, and indicators of ongoing, positive movement.
- **Tertiary (Sage Green):** Reserved for "Acquired" status, successful milestones, and environmentally safe zones.
- **Accent (Warm Copper):** A high-visibility warning color used sparingly for SLA breaches, risk assessment flags, and critical bottlenecks.
- **Background (Linen Off-White):** Provides a soft, paper-like texture to the application background, reducing eye strain during long operational shifts.
- **Surfaces:** Pure white is used for cards and data containers to create a "lifted" appearance over the linen background.

## Typography

This design system utilizes **Inter** for its neutral, highly legible characteristics across both digital displays and printed reports. 

- **Executive Hierarchy:** Large displays and headlines use tighter letter spacing and heavier weights to convey authority.
- **Data Readability:** Body text is set with generous line height to ensure legibility in dense land-record tables.
- **Labels:** Small labels use uppercase with slight tracking to differentiate metadata from content.
- **Monospacing:** For parcel IDs, coordinates, and cadastral numbers, a monospaced font (JetBrains Mono) is recommended to ensure character alignment and prevent misreading of data.

## Layout & Spacing

The design system employs a **12-column fluid grid** for dashboard views and a **fixed-center grid** for administrative forms and reports.

- **The Command Dashboard:** Uses a left-docked sidebar (280px) with a fluid content area. 
- **Density:** To accommodate "Data-rich" requirements, the system supports a "Compact" mode for tables where vertical padding is reduced to 8px.
- **GIS Integration:** Map views should occupy 100% of the viewport width minus the sidebar, with floating control panels positioned 24px from the edges.
- **Rhythm:** All spacing is based on a 4px base unit. Component internal padding should default to 16px (4 units) to maintain a professional, airy feel despite high data density.

## Elevation & Depth

Visual hierarchy is primarily established through **Tonal Layers** rather than heavy shadows, reflecting a modern, flat-enterprise aesthetic.

- **Level 0 (Background):** Linen Off-White (#F8F5EC).
- **Level 1 (Cards/Containers):** Pure White (#FFFFFF) with a 1px border in #E2E8F0. This is the primary surface for data tables and charts.
- **Level 2 (Popovers/Dropdowns):** Pure White with a "GIS-style" shadow: a very soft, diffused ambient shadow (0px 8px 24px rgba(43, 109, 151, 0.1)) tinted with the Primary color.
- **Overlays:** Use a 40% opacity blur (backdrop-filter: blur(4px)) for modal backgrounds to maintain the context of the underlying map or dashboard.

## Shapes

The shape language is "Soft" (0.25rem/4px radius). This choice reflects the precision of engineering and architectural blueprints.

- **Buttons & Inputs:** 4px radius.
- **Cards:** 8px (rounded-lg) for main dashboard modules to provide a subtle distinction from the background.
- **Map Elements:** Map markers and floating GIS controls may use a higher roundedness (pill-shaped) to distinguish "interactive tools" from "data containers."

## Components

Components follow the **shadcn/ui** philosophy: clean, functional, and easily themeable.

- **Enterprise Tables:** Feature sticky headers, zebra-striping using the Linen background color, and status badges using the Primary/Secondary/Tertiary palette.
- **Smart KPI Cards:** Large numeric displays with a subtle topographical contour watermark in the background. Includes a "trend" sparkline in the bottom third.
- **GIS Controls:** Vertical button groups for Zoom In, Zoom Out, Layer Toggle, and Measure. These use a white background with a primary-colored active state.
- **Advanced Filters:** A horizontal bar above tables with "pill" style active filters. Uses Deep Teal for active icons and text.
- **Status Badges:**
  - *Acquired:* Sage Green background, white text.
  - *Pending:* Muted Sea Green background, white text.
  - *At Risk:* Warm Copper background, white text.
- **Buttons:**
  - *Primary:* Solid Deep Teal Blue with white text.
  - *Secondary:* Outlined Deep Teal with 1px border.
  - *Destructive:* Warm Copper with white text.