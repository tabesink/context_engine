# Context Engine Flat Graphite Design Package

This package contains the updated design guidance for the Context Engine WebUI.

## Files

- `DESIGN.md` — updated design system with flatter layout rules, reduced internal boundaries, and Graphite + accent themes.
- `UI_COMPONENT_INVENTORY.md` — extracted WebUI/component inventory and mapping to design decisions.
- `GRAPHITE_ACCENT_TOKENS.css` — token reference for the five Graphite + accent themes.
- `AGENT_IMPLEMENTATION_PROMPT.md` — prompt for a coding agent or junior developer.

## Design intent

The system should feel like a calm, flat, graphite technical workspace. Keep the Ollama-like restraint, but allow subtle accent hints for selected/current/active states.

## Key decision

Use borders for outer containment and interactive controls. Remove internal boxes that are only decorative. Prefer whitespace, dividers, labels, and row rhythm.
