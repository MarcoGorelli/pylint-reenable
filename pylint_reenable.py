from __future__ import annotations

import argparse
import collections
import os.path
import re
import subprocess
import sys
import tempfile
from typing import List
from typing import Match
from typing import Sequence

import tokenize_rt

Tokens = List[tokenize_rt.Token]

_code = r'[a-z-]+(?!\d)'
_sep = r'[,\s]+'
NOQA_RE = re.compile(
    f'# pylint: ?(?:disable|disable-next)=({_code}({_sep}{_code})*)+', re.I,
)
SEP_RE = re.compile(_sep)


def _run_pylint(filename: str) -> dict[int, set[str]]:
    cmd = (
        sys.executable,
        '-mpylint',
        "--msg-template='{line}\t{symbol}",
        filename,
    )
    out, _ = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()
    ret: dict[int, set[str]] = collections.defaultdict(set)
    for line in out.decode().splitlines():
        if (
            line.startswith('*')
            or line.startswith('-')
            or line.startswith('Your code')
            or not line
        ):
            continue
        lineno, code = line.split('\t')
        ret[int(lineno)].add(code)
    return ret


def _remove_comment(tokens: Tokens, i: int) -> None:
    if i > 0 and tokens[i - 1].name == tokenize_rt.UNIMPORTANT_WS:
        del tokens[i - 1: i + 1]
    else:
        del tokens[i]


def _remove_comments(tokens: Tokens) -> Tokens:
    tokens = list(tokens)
    for i, token in tokenize_rt.reversed_enumerate(tokens):
        if token.name == 'COMMENT':
            if NOQA_RE.search(token.src):
                _mask_noqa_comment(tokens, i)
    return tokens


def _mask_noqa_comment(tokens: Tokens, i: int) -> None:
    token = tokens[i]
    match = NOQA_RE.search(token.src)
    assert match is not None

    def _sub(match: Match[str]) -> str:
        return f'# {"."*(len(match.group())-2)}'

    src = NOQA_RE.sub(_sub, token.src)
    tokens[i] = token._replace(src=src)


def _rewrite_noqa_comment(
    tokens: Tokens,
    i: int,
    flake8_results: dict[int, set[str]],
    lints: set[str] | None = None,
) -> None:
    # find logical lines that this noqa comment may affect
    lines: set[int] = set()
    j = i
    while j >= 0 and tokens[j].name not in {'NL', 'NEWLINE'}:
        t = tokens[j]
        if t.line is not None:  # pragma: no branch (tokenize-rt<4.2.1)
            lines.update(range(t.line, t.line + t.src.count('\n') + 1))
        j -= 1

    token = tokens[i]
    disable_next = re.search(r'# pylint: ?disable-next', token.src) is not None

    if lints is None:
        lints = set()
        for line in lines:
            if disable_next:
                lints.update(flake8_results[line + 1])
            else:
                lints.update(flake8_results[line])

    match = NOQA_RE.search(token.src)
    assert match is not None

    def _remove_noqa() -> None:
        assert match is not None
        if match.group() == token.src:
            _remove_comment(tokens, i)
        else:
            src = NOQA_RE.sub('', token.src).strip()
            tokens[i] = token._replace(src=src)

    # exclude all lints on the line but no lints
    if not lints:
        _remove_noqa()
    else:
        codes = set(SEP_RE.split(match.group(1)))
        if 'all' in codes:
            expected_codes = {'all'}
        else:
            expected_codes = codes & lints
        if not expected_codes:
            _remove_noqa()
        elif expected_codes != codes:
            if disable_next:
                comment = (
                    '# pylint: disable-next='
                    f'{", ".join(sorted(expected_codes))}'
                )
            else:
                comment = (
                    '# pylint: disable='
                    f'{", ".join(sorted(expected_codes))}'
                )
            tokens[i] = token._replace(src=NOQA_RE.sub(comment, token.src))


def fix_file(filename: str) -> int:
    with open(filename, 'rb') as f:
        contents_bytes = f.read()

    try:
        contents_text = contents_bytes.decode()
    except UnicodeDecodeError:
        print(f'{filename} is non-utf8 (not supported)')
        return 1

    lines = contents_text.splitlines()

    tokens = tokenize_rt.src_to_tokens(contents_text)

    tokens_no_comments = _remove_comments(tokens)
    src_no_comments = tokenize_rt.tokens_to_src(tokens_no_comments)

    if src_no_comments == contents_text:
        return 0

    fd, path = tempfile.mkstemp(
        dir=os.path.dirname(filename),
        prefix=os.path.basename(filename),
        suffix='.py',
    )
    try:
        with open(fd, 'wb') as f:
            f.write(src_no_comments.encode())
        pylint_results = _run_pylint(path)
    finally:
        os.remove(path)

    if any('syntax-error' in v for v in pylint_results.values()):
        print(f'{filename}: syntax error (skipping)')
        return 0

    for i, token in tokenize_rt.reversed_enumerate(tokens):
        if token.name != 'COMMENT':
            continue
        # check if it's a global disable
        if re.match(r'^# pylint: ?disable=', lines[token.line - 1]):
            lints = {
                i
                for (key, val) in pylint_results.items()
                for i in val
                if key >= token.line
            }
            _rewrite_noqa_comment(tokens, i, pylint_results, lints)
        if re.match(r'^# pylint: ?disable=', lines[token.line - 1].lstrip()):
            # if a whole block is being ignored, then don't rewrite
            continue

        if NOQA_RE.search(token.src):
            _rewrite_noqa_comment(tokens, i, pylint_results)

    newsrc = tokenize_rt.tokens_to_src(tokens)
    if newsrc != contents_text:
        print(f'Rewriting {filename}')
        with open(filename, 'wb') as f:
            f.write(newsrc.encode())
        return 1
    else:
        return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='*')
    args = parser.parse_args(argv)

    retv = 0
    for filename in args.filenames:
        retv |= fix_file(filename)
    return retv


if __name__ == '__main__':
    raise SystemExit(main())
