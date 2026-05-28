# 07 — Acceptance Checklist

## Functional
- [ ] Admin can open Settings → Provider.
- [ ] Provider list shows OpenAI, AWS Bedrock, and Ollama.
- [ ] Each provider row shows name and profile count.
- [ ] Local-only provider can be represented without credential save flow.
- [ ] Clicking a provider row updates the right detail pane.
- [ ] Refresh status action works.
- [ ] Credential can be entered and saved.
- [ ] Saved secret is not shown afterward.
- [ ] Linked model profiles are displayed in the detail pane.

## Visual
- [ ] Layout matches Option C2 intent.
- [ ] Rows are flatter and more borderless than current UI.
- [ ] Selected provider row uses soft accent background + left accent bar.
- [ ] Heavy nested cards are removed.
- [ ] Health summary uses subtle dividers, not noisy cards.
- [ ] Detail pane feels airy and clean.

## UX
- [ ] Loading states are local and non-jarring.
- [ ] Errors are understandable and recoverable.
- [ ] Save action clearly communicates pending/success/error.
- [ ] Refresh action does not block whole page.

## Accessibility
- [ ] Interactive rows are keyboard reachable.
- [ ] Inputs and buttons have visible focus states.
- [ ] Icons are not the only means of conveying state.
- [ ] Color contrast is adequate.
