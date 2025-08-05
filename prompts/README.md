# 🎯 AI Prompt Configuration System

This directory contains structured prompt templates for different migration scenarios.

## 📁 **Directory Structure**

```
prompts/
├── migration/           # Code migration prompts
│   ├── action_to_controller.yaml
│   ├── form_to_model.yaml
│   ├── service_migration.yaml
│   └── config_migration.yaml
├── validation/          # Code validation prompts
│   ├── quality_check.yaml
│   ├── spring_compliance.yaml
│   └── business_logic_validation.yaml
├── error_resolution/    # Error fixing prompts
│   ├── compilation_errors.yaml
│   ├── runtime_errors.yaml
│   └── dependency_errors.yaml
├── analysis/           # Code analysis prompts
│   ├── pattern_detection.yaml
│   ├── complexity_assessment.yaml
│   └── risk_analysis.yaml
└── learning/           # Learning enhancement prompts
    ├── pattern_extraction.yaml
    ├── knowledge_synthesis.yaml
    └── prompt_enhancement.yaml
```

## 🔧 **Prompt Template Format**

Each YAML file contains:
- **metadata**: Description, version, author
- **templates**: Multiple prompt variations
- **parameters**: Configurable placeholders
- **examples**: Sample inputs/outputs
- **validation**: Success criteria

## 📊 **Benefits**

✅ **Maintainable**: Easy to update without code changes
✅ **Version Control**: Track prompt evolution
✅ **A/B Testing**: Multiple template variations
✅ **Customizable**: Environment-specific prompts
✅ **Collaborative**: Team can contribute improvements
✅ **Learning Integration**: Prompts improve based on success metrics
