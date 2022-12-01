[![Build Status](https://dev.azure.com/MarcoGorelli/MarcoGorelli/_apis/build/status/MarcoGorelli.pylint-reenable?branchName=main)](https://dev.azure.com/MarcoGorelli/MarcoGorelli/_build/latest?definitionId=53&branchName=main)
[![Azure DevOps coverage](https://img.shields.io/azure-devops/coverage/MarcoGorelli/MarcoGorelli/53/main.svg)](https://dev.azure.com/MarcoGorelli/MarcoGorelli/_build/latest?definitionId=53&branchName=main)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MarcoGorelli/pylint-reenable/main.svg)](https://results.pre-commit.ci/latest/github/MarcoGorelli/pylint-reenable/main)

pylint-reenable
===============

A tool (and pre-commit hook) to automatically remove unnecessary `# pylint: disable`
comments, for example: a check that's no longer applicable (say you increased your
max line length), a mistake (`# pylint: disable` added to a line that wasn't failing),
or other code in the file caused it to no longer need a `# pylint: disable` (such as an unused import).

NOTE: this is lifted from [yesqa](https://github.com/asottile/yesqa), whose license is included here (as per its terms).

## Installation

Coming soon...

## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/MarcoGorelli/pylint-reenable
    rev: v0.1.0
    hooks:
    -   id: pylint-reenable
```

If you need to select a specific version of pylint and/or run with specific
pylint plugins, add them to [`additional_dependencies`][0].

[0]: http://pre-commit.com/#pre-commit-configyaml---hooks
