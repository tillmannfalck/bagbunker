#!/usr/bin/env python

INDEX_TEMPLATE = """\
<div class="container apps">
    <div class="row">
ROWS
    </div>
</div>
"""

ROW_TEMPLATE = """\
        <div class="col-xs-6">
            {{#link-to 'NAME'}}
                <img class="img-responsive img-rounded" src="app/styles/images/NAME.jpg">
            {{/link-to}}
            {{#link-to 'NAME' class="btn btn-default btn-block"}}NAME{{/link-to}}
        </div>\
"""

import sys
names = [x for x in (x.split('/')[-2] for x in sys.argv[1:])
         if x != 'marv']

print INDEX_TEMPLATE.replace('ROWS', '\n'.join([
    ROW_TEMPLATE.replace('NAME', x) for x in names
]))
