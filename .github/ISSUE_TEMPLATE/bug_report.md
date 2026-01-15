name: 🐛 Bug Report
description: Report a bug or issue
title: "[BUG] "
labels: ["bug", "needs-triage"]
assignees: []

body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to report a bug! Please fill out this form as completely as possible.

  - type: input
    id: title
    attributes:
      label: Bug Title
      description: Brief description of the bug
      placeholder: "Ex: Order placement fails with 'Connection refused'"
    validations:
      required: true

  - type: textarea
    id: description
    attributes:
      label: Description
      description: Detailed description of the bug
      placeholder: "Describe what happened..."
    validations:
      required: true

  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
      description: Steps to reproduce the bug
      placeholder: |
        1. Start application
        2. Configure broker settings
        3. Click on place order
        4. See error...
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What should happen
      placeholder: "Order should be placed successfully..."
    validations:
      required: true

  - type: textarea
    id: actual
    attributes:
      label: Actual Behavior
      description: What actually happens
      placeholder: "Error message shown: ..."
    validations:
      required: true

  - type: textarea
    id: error
    attributes:
      label: Error Messages / Logs
      description: Paste any error messages or relevant logs
      render: bash

  - type: input
    id: version
    attributes:
      label: Angel-X Version
      description: Version of Angel-X you're using
      placeholder: "2.0.0"
    validations:
      required: true

  - type: input
    id: python
    attributes:
      label: Python Version
      description: Output of `python --version`
      placeholder: "3.11.0"
    validations:
      required: true

  - type: input
    id: os
    attributes:
      label: Operating System
      description: OS and version
      placeholder: "Ubuntu 22.04, macOS 13, Windows 11"
    validations:
      required: true

  - type: textarea
    id: environment
    attributes:
      label: Environment
      description: Relevant environment details (Docker, Cloud, VPS, etc.)
      placeholder: "Docker on Ubuntu 22.04 LTS"

  - type: textarea
    id: screenshots
    attributes:
      label: Screenshots
      description: Add screenshots if applicable

  - type: checkboxes
    id: checklist
    attributes:
      label: Checklist
      options:
        - label: I have searched for existing issues
          required: true
        - label: I am using the latest version
          required: true
        - label: I have provided all requested information
          required: true
