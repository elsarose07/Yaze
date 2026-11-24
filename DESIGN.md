# Design System: Studio Minimalist

<!-- impeccable:design-schema 1 -->

## Visual World

Studio Minimalist is an architectural, restrained design language built for technical desktop instrumentation. It rejects gratuitous glowing effects, fake sparklines, and generic card clutter in favor of deep graphite surfaces, crisp contrast, precise tabular typography, and intentional telemetry signal pulses.

### Color Palette

- **Canvas Background**: `#121214` (Deep graphite)
- **Sidebar Surface**: `#0E0E10` (Recessed obsidian rail)
- **Card / Surface**: `#18181B` (Zinc-900 surface panels)
- **Surface Hover**: `#202024` (Subtle tactile shift)
- **Surface Selected / Active**: `#27272A`
- **Subtle Borders**: `#27272A` (1px clean architectural perimeter)
- **Highlight Borders**: `#3F3F46` (Active / focused input boundary)
- **Typography Primary**: `#FFFFFF` (Crisp pure white headings, metric values)
- **Typography Secondary**: `#A1A1AA` (Zinc-400 labels, descriptions)
- **Typography Muted**: `#71717A` (Zinc-500 captions, timestamp notes)

### Telemetry Signal Accents

- **Download Stream**: `#38BDF8` (Sky / Electric Cyan)
- **Upload Stream**: `#10B981` (Emerald Green)
- **Latency / Warning**: `#F59E0B` (Vibrant Amber)
- **Danger / Critical**: `#EF4444` (Crimson)
- **Accent Primary**: `#2563EB` (Royal Blue for primary triggers)

### Typography

- **Font Family**: `"Segoe UI", -apple-system, BlinkMacSystemFont, "SF Pro Display", sans-serif`
- **Monospace / Metric Data**: `"Consolas", "SF Mono", "Cascadia Code", monospace`
- **Scale**:
  - Hero Metric: `26px`, Bold, `#FFFFFF`
  - Large Metric: `18px`, Bold, `#FFFFFF`
  - Section Title: `14px`, SemiBold, `#FFFFFF`
  - Nav Label: `13px`, Medium, `#A1A1AA` (Active: `#FFFFFF`)
  - Body & Table: `12px`, Regular, `#F4F4F5`
  - Caption & Badges: `11px`, Medium, `#71717A`

### Navigation & Layout Architecture

- **Vertical Navigation Rail**: A permanent 200px left-hand dock housing:
  - App Header Brand (`⚡ YAZE` + live status indicator pill)
  - Vertical Navigation Action List (`Overview`, `Applications`, `Analytics`, `Speed Test`, `Settings`)
  - Bottom Utility Dock (Active interface pill, "Minimize to Tray" action)
- **Content Workspace**: High-efficiency multi-panel layout maximizing vertical space for the real-time oscilloscope and telemetry tables.

### Craft Floor Enforcements

- **No Eyebrows / Kickers**: Delete fake subtitle labels above headings.
- **No Zero-Offset Colored Halos**: Shadows use subtle offset and soft alpha.
- **No Generic Sparkline Placeholders**: Actual dynamic QPainter rolling canvas with autoscale grid and peak indicators.
- **State Completeness**: Every button, navigation item, and table row defines default, hover, pressed, active, and disabled states.
- **Operate Mode Restraint**: Zero decorative loading animations; instant transition and high scanability.
