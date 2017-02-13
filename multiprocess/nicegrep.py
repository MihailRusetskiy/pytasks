import sys, os
from argparse import ArgumentParser, FileType
from multiprocessing import Pool
from itertools import chain
import functools


PROC_COUNT = 2
LINES_PER_PROC = 40
LINES_PER_CYCLE = LINES_PER_PROC * PROC_COUNT
GREEN = '\033[32m'
PRETTY_GREEN = '\033[92m'
END_COLOR = '\033[0m'


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


def index_find(pattern, string):
    """Find index of pattern match in string. Returns -1 if not found."""
    pattern = pattern.lower()
    string = string.lower()

    for i in range(len(string)):
        for j in range(len(pattern)):
            if string[i+j] != pattern[j]:
                break
            elif j == len(pattern) - 1:
                return i
    return -1


def color_find(pattern, string):
    """Find all matches of pattern in string. Returns colored string, or empty string if not found."""
    result = ''
    index = index_find(pattern, string)

    while index != -1:
        result += string[:index]
        result += PRETTY_GREEN + string[index:index + len(pattern)] + END_COLOR
        string = string[index + len(pattern):]
        index = index_find(pattern, string)

    return result if result == '' else result + string


def get_match(lines, pattern):
    """Find the pattern in the string. Returns the match result or the empty string if not found."""
    indexes = []
    for line in lines:
        index = color_find(pattern, line)
        indexes.append(index)
    return indexes


def print_result(print_header, header, print_lineno, lineno, print_line, line):
    """Print result to standard output."""
    result = ''
    if print_header:
        result += '%s' % header
    if print_lineno:
        if len(result) > 0:
            result += ':'
        result += '%d' % (lineno + 1)
    if print_line:
        if len(result) > 0:
            result += ':'
        result += line
    sys.stdout.write('%s\n' % result.strip('\n'))


def grep_file(pool, filename, pattern, print_headers, print_lineno, print_lines):
    """Search a single file or standard input."""

    get_matchs = functools.partial(get_match, pattern=pattern)
    text = sys.stdin if filename == '(standard input)' else open(filename, 'r')
    line = text.readline()
    lineno = 1
    lines = []
    while line:
        lines.append(line)
        if lineno % (LINES_PER_CYCLE) == 0:
            results = pool.map(get_matchs, chunks(lines, LINES_PER_PROC))
            for ln, result in enumerate(chain.from_iterable(results), start=(lineno - LINES_PER_CYCLE)):
                if result:
                    print_result(print_headers, filename, print_lineno, ln, print_lines, result)
            lines = []
        line = text.readline()
        lineno += 1
    text.close()


def grep_files(pool, paths, pattern, recurse, print_headers,
                print_lineno, print_line):
    """Search files and directories."""
    for path in paths:
        if os.path.isfile(path) or path == '(standard input)':
            grep_file(pool, path, pattern, print_headers, print_lineno, print_line)
        else:
            if recurse:
                more_paths = [path + '/' + child for child in os.listdir(path)]
                grep_files(pool, more_paths, pattern, recurse, print_headers, print_lineno, print_line)
            else:
                sys.stdout.write('grep: %s: Is a directory\n' % path)


def setup_parser():
    """Configure command line argument parser object."""
    parser = ArgumentParser(description='Find matches of a pattern in ' \
                            'lines of file(s).', add_help=False)
    parser.add_argument('-n', '--line-number', action='store_true', help='print line numbers, indexed from 1')
    parser.add_argument('-R', '-r', '--recursive', action='store_true', help='recursively search directories', default=False)
    parser.add_argument('pattern', type=str, help='the pattern to find')
    parser.add_argument('files', metavar='FILES', nargs='*', default=['-'],
                        help='the files(s) to search')
    return parser


DEFAULT_PRINT_OPTIONS = (True, False, True)

def main():
    parser = setup_parser()
    args = parser.parse_args()
    print_headers, print_lineno, print_lines = DEFAULT_PRINT_OPTIONS
    print_lineno = args.line_number
    pattern = args.pattern
    pool = Pool(PROC_COUNT)
    files = [f if f!= '-' else '(standard input)' for f in args.files]

    grep_files(pool, files, pattern, args.recursive, print_headers, print_lineno, print_lines)

if __name__ == '__main__':
    main()
