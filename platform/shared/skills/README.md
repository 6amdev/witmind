# WitMind.AI Skills Library

This directory contains reusable skills that can be used by AI agents.

## Structure

```
skills/
├── coding/           # Code generation skills
│   ├── react/
│   ├── nextjs/
│   ├── python/
│   └── nodejs/
├── devops/           # DevOps and deployment skills
│   ├── docker/
│   ├── kubernetes/
│   └── ci-cd/
├── testing/          # Testing skills
│   ├── unit-tests/
│   ├── e2e-tests/
│   └── load-tests/
└── documentation/    # Documentation skills
    ├── api-docs/
    ├── readme/
    └── changelog/
```

## Usage

Skills are loaded by agents based on their configuration and the task requirements.

Example skill structure:
```yaml
skill:
  id: react-component
  name: "React Component Generator"
  description: "Generates React components with TypeScript"

  inputs:
    - name: component_name
      type: string
      required: true
    - name: props
      type: object
      required: false

  outputs:
    - type: file
      pattern: "*.tsx"

  prompts:
    system: "prompts/react-component-system.md"
    user: "prompts/react-component-user.md"
```

## Adding New Skills

1. Create a new directory under the appropriate category
2. Add a `skill.yaml` configuration file
3. Add prompt templates in `prompts/` subdirectory
4. Add example outputs in `examples/` subdirectory
5. Document usage in a `README.md` file
