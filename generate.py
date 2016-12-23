#!/usr/bin/env python

from __future__ import print_function, unicode_literals

import argparse
import json
import sys
from collections import OrderedDict
from datetime import (
    datetime,
    timedelta,
)
from distutils.version import LooseVersion as Version


RED = (255, 204, 204)
YELLOW = (255, 255, 153)
GREEN = (204, 255, 153)
GREENER = (153, 255, 153)

DISTROS = ('fedora', 'rhel', 'opensuse', 'debian', 'ubuntu')


def format_date(text):
    if text is None:
        return '?'
    try:
        d = datetime.strptime(text, '%Y-%m')
        return d.strftime('%b %Y')
    except ValueError:
        # For q1/q2
        y, m = text.split('-')
        return '%s %s' % (m, y)


def distro_key(name):
    base_name = name.split()[0]
    try:
        return DISTROS.index(base_name.lower()), name
    except ValueError:
        return sys.maxsize, name


def print_cell(text, color=None):
    if color:
        print('  <td style="background-color: rgb(%d, %d, %d);">%s</td>'
              % (color + (text,)))
    else:
        print('  <td>%s</td>' % text)


def main(args):
    with open('requirements.json') as fh:
        requirements = json.load(fh)

    checked_requirements = []
    for color, ver in (
            (YELLOW, args.esr),
            (GREEN, args.release),
            (GREENER, args.release + 3)):
        ver = str(ver)
        if ver not in requirements:
            raise Exception('Missing requirements for version %s' % ver)
        checked_requirements.append((color, requirements[ver]))

    with open('distro_data.json') as fh:
        distro_data = json.load(fh)

    print('<table>')

    now = datetime.now()
    last_month = now - timedelta(days=now.day)

    for distro, data in sorted(distro_data.items(),
                               key=lambda d: distro_key(d[0])):
        print('<tr>')

        compat = OrderedDict(
            (k, RED) for k in ('glibc', 'glib', 'gtk+2', 'gtk+3', 'pixman',
                               'stdc++', 'GCC'))

        versions = data.get('versions', {})
        for color, req in checked_requirements:
            for name in compat:
                distro_ver = versions.get(name) or '0'
                ver = req.get(name) or '0'
                if not isinstance(distro_ver, list):
                    distro_ver = [distro_ver]
                if any(Version(v) >= ver for v in distro_ver):
                    compat[name] = color

        runtime_compat = [c for n, c in compat.items() if n != 'GCC']
        for color in (RED, YELLOW, GREEN, GREENER):
            if color in runtime_compat:
                print_cell(distro, color)
                break

        for name, color in compat.items():
            text = versions.get(name) or 'N/A'
            if isinstance(text, list):
                text = ', '.join(text)
            print_cell(text, color)

        release = data.get('release', {})
        print_cell(format_date(release.get('date')))
        eol = release.get('eol')
        lts = release.get('lts')
        if lts:
            text = '%s / %s (LTS)' % (format_date(eol), format_date(lts))
            eol = lts
        else:
            text = format_date(eol)
        if eol:
            try:
                d = datetime.strptime(eol, '%Y-%m')
            except:
                d = now
            eol = RED if d < last_month else None
        print_cell(text, eol)

        print('</tr>')

    print('</table>')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('esr', type=int,
                        help='version number of the current ESR')
    parser.add_argument('release', type=int,
                        help='version number of the current release')

    args = parser.parse_args()

    main(args)
