name: ✨ Feature Request
description: Suggest a new feature or enhancement
title: "[FEATURE] "
labels: ["enhancement", "needs-triage"]
assignees: []

body:
  - type: markdown
    attributes:
      value: "## Feature Request"

  - type: input
    id: title
    attributes:
      label: Feature Title
      description: Brief description of the feature
      placeholder: "Support for multi-leg strategy management"
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Description
      description: Detailed description of the feature
      placeholder: "Describe the feature you want to see..."
    validations:
      required: true

  - type: textarea
    id: problem
    attributes:
      label: Problem It Solves
      description: What problem does this feature solve?
      placeholder: "Currently users cannot..."
    validations:
      required: true

  - type: textarea
    id: solution
    attributes:
      label: Proposed Solution
      description: How should this feature work?
      placeholder: "Implement a UI component that..."

  - type: textarea
    id: alternatives
    attributes:
      label: Alternative Solutions
      description: Any alternative approaches?

  - type: textarea
    id: examples
    attributes:
      label: Use Cases / Examples
      description: Examples of how this feature would be used

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: I have checked for existing feature requests
          required: true
        - label: This feature aligns with Angel-X goals
          required: true
