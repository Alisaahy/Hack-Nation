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
