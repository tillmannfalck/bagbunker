/*
 * Copyright 2015 Ternaris, Munich, Germany
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

import Ember from 'ember';


const formatters = {};

export default Ember.Component.extend({
    classNames: ['table-responsive'],

    turbo: 2,

    ascending: true,
    sort: null,

    columns: [],
    rows: [],

    initializeModel: Ember.on('init', Ember.observer('model', function() {
        const rows = this.get('model.rows');
        const sort = this.get('model.sort');
        const ascending = this.get('model.ascending');

        this.beginPropertyChanges();

        if (rows.length) {
            this.set('columns', rows[0].columns.map(c => {
                return { title: c.title };
            }));

            this.set('rows', rows.map(row => {
                return {
                    columns: row.columns.map(col => {
                        if (!formatters[col.formatter]) {
                            const name = `helper:formatter-${col.formatter}`;
                            const helper = this.container.lookupFactory(name);
                            formatters[col.formatter] = helper;
                        }

                        let formatter = formatters[col.formatter];

                        col.formatted = col.list ?
                            col.value
                                .map(val => formatter.compute([val], {}))
                                .join('') :
                            formatter.compute([col.value], {});

                        return col;
                    }),
                    id: row.id
                };
            }));

            if (sort && this.get('sort') === null) {
                var index = rows[0].columns.getEach('name').indexOf(sort);
                this.set('sort', index);
                if (typeof ascending === 'boolean') {
                    this.set('ascending', ascending);
                }
            }
        } else {
            this.set('columns', []);
            this.set('rows', []);
        }

        this.endPropertyChanges();
    })),

    sorted: Ember.computed('sort', 'ascending', 'rows', function() {
        const rows = this.get('rows');
        const sort = this.get('sort');
        const ascending = this.get('ascending');

        if (sort === null) {
            return rows;
        }

        var defined = rows.filter(row =>
            typeof row.columns[sort].value !== 'undefined'
        );

        var notdefined = rows.filter(row =>
            typeof row.columns[sort].value === 'undefined'
        );

        var sorted = defined.sort(function(l, r) {
            l = l.columns[sort].value;
            r = r.columns[sort].value;
            if (typeof l === 'object') {
                if (l instanceof Array) {
                    l = l.length;
                } else if (l === null) {
                    l = '';
                } else {
                    l = l.title;
                }
            } else if (typeof l === 'undefined') {
                l = '';
            }
            if (typeof r === 'object') {
                if (r instanceof Array) {
                    r = r.length;
                } else if (r === null) {
                    r = '';
                } else {
                    r = r.title;
                }
            } else if (typeof r === 'undefined') {
                r = '';
            }

            if (ascending) {
                return (l>=r) * 2 - 1;
            } else {
                return (l<r) * 2 - 1;
            }
        });
        return sorted.concat(notdefined);
    }),

    page: 0,
    pagesize: null,

    numPages: Ember.computed('sorted', 'pagesize', function() {
        const pagesize = this.get('pagesize');
        if (pagesize === null) {
            return 1;
        }
        return Math.ceil(this.get('sorted').length / this.get('pagesize'));
    }),

    paginated: Ember.computed('sorted', 'page', 'pagesize', function() {
        const page = this.get('page');
        const pagesize = this.get('pagesize');
        if (pagesize === null) {
            return this.get('sorted');
        }
        return this.get('sorted').slice(page * pagesize, (page + 1) * pagesize);
    }),

    allChecked: Ember.computed('paginated.@each.checked', function() {
        return this.get('paginated').isEvery('checked', true);
    }),

    tbody: Ember.computed('isSelecting', 'paginated', function() {
        var isSelecting = this.get('isSelecting');
        Ember.run.next(function() {
            Ember.$('[data-toggle="tooltip"]').tooltip();
        });

        const page = this.get('page');
        const pagesize = this.get('pagesize') || 0;
        return this.get('paginated').reduce(function(l, r, i) {
            var select = isSelecting ?
                '<td><span class="m-checkbox' +
                    (r.checked?' checked':'') +
                    '" data-index="'+ (page * pagesize + i) +'"></span></td>' :
                '';
            return l.concat([
                '<tr>',
                select,
                r.columns.reduce(function(l, r) {
                    return l.concat([
                        '<td>',
                        r.formatted,
                        '</td>'
                    ]);
                }, []).join(''),
                '</tr>'
            ]);
        }, []).join('');
    }),

    click: function(e) {
        if (e.target.tagName === 'A' && e.target.dataset.route) {
            e.preventDefault();
            e.stopPropagation();
            this.container.lookup('route:application')
                .transitionTo(e.target.dataset.route, e.target.dataset.id);
        } else if (e.target.classList.contains('m-checkbox')) {
            this.send('select', e.target.dataset.index);
        }
    },

    actions: {
        prevPage() {
            const page = this.get('page');
            if (page > 0) {
                this.decrementProperty('page');
            }
        },
        nextPage() {
            const page = this.get('page');
            const numPages = this.get('numPages');
            if (page < numPages - 1) {
                this.incrementProperty('page');
            }
        },
        sort: function(index) {
            var prev = this.get('sort');
            if (prev === index) {
                this.toggleProperty('ascending');
            } else {
                this.set('ascending', true);
                this.set('sort', index);
            }
        },

        row: function(row) {
            this.sendAction('rowClicked', row);
        },

        select: function(index) {
            if (~index) {
                var row = this.get('sorted')[index];
                Ember.set(row, 'checked', !row.checked);
                this.$()
                    .find('[data-index=' + index + ']')
                    .toggleClass('checked');
            } else {
                this.get('sorted').setEach('checked', !this.get('allChecked'));
                if (this.get('allChecked')) {
                    this.$().find('[data-index]').addClass('checked');
                } else {
                    this.$().find('[data-index]').removeClass('checked');
                }
            }
            this.sendAction('checked', this.get('sorted'));
        }
    }
});
