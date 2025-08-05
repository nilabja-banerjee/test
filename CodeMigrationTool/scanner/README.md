# Scanner Module

## Purpose
This module scans legacy Java codebases built with Struts 1.x and Spring 1.x to:
- Identify and classify all `.java`, `.jsp`, `.xml`, and `.properties` files
- Build call graphs and class dependencies
- Extract interface implementations and bean/service layers
- Parse `struts-config.xml` and `tiles-defs.xml` for AI-ready migration context

## How to Run
```bash
cd CodeMigrationTool
python3 -m scanner.engine.main
