from __future__ import annotations

import pytest

import pylint_reenable


@pytest.fixture
def assert_rewrite(tmpdir):
    def _assert(s, expected=None):
        expected_retc = 0 if expected is None else 1
        expected = s if expected is None else expected
        f = tmpdir.join('f.py')
        f.write(s)
        assert pylint_reenable.fix_file(str(f)) == expected_retc
        assert f.read() == expected

    return _assert


def test_non_utf8_bytes(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write_binary('x = "€"'.encode('cp1252'))
    assert pylint_reenable.fix_file(str(f)) == 1
    out, _ = capsys.readouterr()
    assert out == f'{f} is non-utf8 (not supported)\n'


@pytest.mark.parametrize(
    'src',
    (
        '',  # noop
        '# hello\n',  # comment at beginning of file
        # still needed
        'import os  # pylint: disable=unused-import\n',
        'import os  # NOQA\n',
        'import os  # noqa: F401\n',
        'import os  # noqa:F401\n',
        'import os  # noqa: F401 isort:skip\n',
        'import os  # isort:skip # noqa\n',
        'import os  # isort:skip # noqa: F401\n',
        '"""\n' + 'a' * 40 + ' ' + 'b' * 60 + '\n""" # noqa\n',
        'from foo\\\nimport bar  # noqa\n',
        # don't rewrite syntax errors
        'import x  # noqa\nx() = 5\n',
        'A' * 65 + ' = int\n\n\n'
        'def f():\n'
        '    # type: () -> ' + 'A' * 65 + '  # noqa\n'
        '    pass\n',
        'def foo(w: Sequence[int], x: Sequence[int], y: int, z: int) -> bar: ...  # noqa: E501, F821\n',
        'def foo(w: Sequence[int]) -> bar:  # foobarfoobarfoobarfoobarfoobarfoo   # noqa: E501, F821\n',
        '1 = 3  # pylint: disable=all\n',
    ),
)
def test_ok(assert_rewrite, src):
    assert_rewrite(src)


@pytest.mark.parametrize(
    ('src', 'expected'),
    (
        # line comments
        ('x = 1  # pylint:disable=redefined-outer-name\n', 'x = 1\n'),
        (
            'import os  # pylint: disable=unused-import,foobar\n',
            'import os  # pylint: disable=unused-import\n',
        ),
        (
            'import os  # pylint:disable=unused-import,foobar\n',
            'import os  # pylint: disable=unused-import\n',
        ),
        (
            'import os  # pylint:disable=all,foobar\n',
            'import os  # pylint: disable=all\n',
        ),
        (
            '# foo # pylint:disable-next=redefined-outer-name\nx = 1\n',
            '# foo\nx = 1\n',
        ),
        (
            '# pylint:disable=redefined-outer-name # foo\nx = 1\n',
            '# foo\nx = 1\n',
        ),
        (
            'try:\n'
            '    pass\n'
            'except OSError:  # pylint:disable=redefined-outer-name hi\n'
            '    pass\n',
            'try:\n' '    pass\n' 'except OSError:\n' '    pass\n',
        ),
        (
            'import os  # pylint:disable=unused-import\n'
            '# hello world\n'
            'os\n',
            'import os\n' '# hello world\n' 'os\n',
        ),
        (
            '# a  # pylint: disable=redefined-outer-name\n',
            '# a\n',
        ),
        pytest.param(
            'if x==1:  # pylint:disable=foo\n' '    pass\n',
            'if x==1:\n' '    pass\n',
            id='wrong noqa',
        ),
        pytest.param(
            'x = 1  # foo # pylint: disable=ABC\n',
            'x = 1  # foo\n',
            id='multi-character noqa code',
        ),
        (
            'if True:\n'
            '    # pylint: disable-next=invalid-name\n'
            '    pass\n',
            'if True:\n' '\n' '    pass\n',
        ),
        (
            'if True:  '
            '# pylint: disable-next=invalid-name,redefined-outer-name\n'
            '    x=1\n',
            'if True:  # pylint: disable-next=invalid-name\n' '    x=1\n',
        ),
        ('# pylint: disable-next=unused-import\nx = 1\n', '\nx = 1\n'),
        # file comments
        ('# pylint: disable=unused-import\nx = 1\n', '\nx = 1\n'),
        ('x = 1  # pylint: disable=red\n', 'x = 1\n'),
    ),
)
def test_rewrite(assert_rewrite, src, expected):
    assert_rewrite(src, expected)


def test_main(tmpdir, capsys):
    f = tmpdir.join('f.py').ensure()
    g = tmpdir.join('g.py')
    g.write('x = 1  # pylint: disable=foo\n')
    ret = pylint_reenable.main((str(f), str(g)))
    assert ret == 1
    assert g.read() == 'x = 1\n'
    out, _ = capsys.readouterr()
    assert out == f'Rewriting {g}\n'


def test_show_source_in_config(tmpdir, capsys):
    f = tmpdir.join('f.py')
    f.write('import os  # noqa\n')
    tmpdir.join('tox.ini').write('[flake8]\nshow_source = true\n')
    with tmpdir.as_cwd():
        ret = pylint_reenable.main((str(f),))
    assert ret == 0
    assert f.read() == 'import os  # noqa\n'
