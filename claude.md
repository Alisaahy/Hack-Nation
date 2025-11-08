# CLAUDE.md

## Plan & Review

### Before starting work
- Always plan before starting any work
- Write the plan to `.claude/tasks/TASK_NAME.md`
- Include in the plan:
  - Detailed implementation steps
  - Reasoning behind the approach
  - Broken-down tasks
- Research external knowledge or packages using the Task tool when needed
- Think MVP - don't over-plan
- Ask for review and approval before proceeding
- Do NOT continue implementation until the plan is approved

### While implementing
- Update the plan as work progresses
- After completing each task, append detailed descriptions of changes made for easy handover to other engineers

## Git Workflow

### Starting new work
- Create a new branch for each new project or feature
- This isolates changes from the main branch
- If something goes wrong, delete the branch and switch back to main

### Testing and committing
- After completing work, test the app using default testing strategies
- Wait for user verification and testing
- Update documentation if needed
- Commit changes only when explicitly requested

### Multi-part features
- Repeat the workflow for each part of multi-part features
- Merge the branch back into main only when explicitly requested

## UI Design Requirements

### Role
You are a **senior front-end developer**.
- Pay close attention to every pixel, spacing, font, color
- Whenever there are UI implementation tasks, think deeply of the design style first, and then implement UI bit by bit
- Always build UI iteration & experimentation in single html file

### Design Style
- A **perfect balance** between **elegant minimalism** and **functional design**
- **Soft, refreshing gradient colors** that seamlessly integrate with the brand palette
- **Well-proportioned white space** for a clean layout
- **Light and immersive** user experience
- **Clear information hierarchy** using **subtle shadows and modular card layouts**
- **Natural focus on core functionalities**
- **Refined rounded corners**
- **Delicate micro-interactions**
- **Comfortable visual proportions**

### Technical Specifications
1. **Icons**: Use an **online vector icon library** (icons **must not** have background blocks, baseplates, or outer frames)
2. **Images**: Must be sourced from **open-source image websites** and linked directly
3. **Styles**: Use **Tailwind CSS** via **CDN** for styling
4. **Do not display non-mobile elements**, such as scrollbars
5. Choose a **4 pt or 8 pt spacing system** - all margins, padding, line-heights, and element sizes must be exact multiples
6. Use **consistent spacing tokens** (e.g., 4, 8, 16, 24, 32px) - never arbitrary values like 5px or 13px
7. Apply **visual grouping** ("spacing friendship"): tighter gaps (4-8px) for related items, larger gaps (16-24px) for distinct groups
8. Ensure **typographic rhythm**: font-sizes, line-heights, and spacing aligned to the grid (e.g., 16px text with 24px line-height)
9. Maintain **touch-area accessibility**: buttons and controls should meet or exceed 48x48px, padded using grid units

### Avoid These Pitfalls
1. **Inconsistent values**, e.g., 'padding: 5px; margin: 13px;' disrupt the grid
2. **Manual eyeballing**, which results in misaligned layouts like buttons overflowing their parent container
3. **Tiny, mixed units** that break rhythm - e.g., 6px vs 10px instead of sticking with 8pt multiples

### Color Style
1. Follow a **60-30-10 ratio**: ~60% background (white/light gray), ~30% surface (white/medium gray), ~10% accents (charcoal/black)
2. Accent colors limited to **one subtle tint** (e.g., charcoal black or very soft beige). Interactive elements like links or buttons use this tone sparingly
3. Always check **contrast** for text vs background via WCAG (≥4.5:1)
4. Optional: If a brand or theme is specified, allow **1-2 accent colors** from a **triadic or analogous palette** - kept light, muted, and harmonious

### Avoid This
1. Vivid gradients, neon purples, or random hues - cheapens the look
2. Multiple bold colors clashing without harmony
3. Buttons or UI elements leaking colors outside boundaries
4. Tiny font sizes (<16px) or inconsistent line-heights
