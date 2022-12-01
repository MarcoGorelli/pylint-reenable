[![Build Status](https://github.com/MarcoGorelli/pylint-reenable/workflows/tox/badge.svg)](https://github.com/MarcoGorelli/auto-walrus/actions?workflow=tox)
[![Coverage](https://codecov.io/gh/MarcoGorelli/auto-walrus/branch/main/graph/badge.svg)](https://codecov.io/gh/MarcoGorelli/auto-walrus)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/MarcoGorelli/pylint-reenable/main.svg)](https://results.pre-commit.ci/latest/github/MarcoGorelli/pylint-reenable/main)


pylint-reenable
===============

A tool (and pre-commit hook) to automatically remove unnecessary `# pylint: disable`
comments, for example: a check that's no longer applicable (say you increased your
max line length), a mistake (`# pylint: disable` added to a line that wasn't failing),
or other code in the file caused it to no longer need a `# pylint: disable` (such as an unused import).

NOTE: this is lifted from [yesqa](https://github.com/asottile/yesqa), whose license is included here (as per its terms).

## Installation

```
pip install pylint-reenable
```

## Command-line example

```console
$ pylint-reenable my_file.py
```

## As a pre-commit hook

See [pre-commit](https://github.com/pre-commit/pre-commit) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/MarcoGorelli/pylint-reenable
    rev: v0.1.4
    hooks:
    -   id: pylint-reenable
```

If you need to select a specific version of pylint and/or run with specific
pylint plugins, add them to [`additional_dependencies`][0].

[0]: http://pre-commit.com/#pre-commit-configyaml---hooks
