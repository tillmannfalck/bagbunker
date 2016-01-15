#!/usr/bin/env python

TEMPLATE = """\
{
    "name": "Bagbunker",
    "proxy": [{"pattern": "^/marv", "target": "http://localhost:5000"}],
    "csp": {
        "styleSrc": ["'self'", "'unsafe-inline'"]
    },
    "overlays": [
OVERLAYS
    ],
    "stylefiles": [
        "main.scss",
STYLEFILES
    ]
}
"""

import sys
paths = [x for x in sys.argv[1:]
         if '/marv/' not in x]

overlays = [8*' ' + '"{}"'.format(x) for x in paths]

stylefiles = [8*' ' + '"{}.scss"'.format(x.split('/')[-2]) for x in paths]

print TEMPLATE.replace('OVERLAYS', ',\n'.join(overlays))\
              .replace('STYLEFILES', ',\n'.join(stylefiles))
