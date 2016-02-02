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

export default Ember.Controller.extend({
    application: Ember.inject.controller(),
    session: Ember.inject.service(),

    queryParams: [ 'filter', 'autoupdate', 'debugfilters' ],

    filter: '',
    filterObj: {},

    autoupdate: false,
    showfilters: true,
    debugfilters: false,

    checked: [],
    isSelecting: false,

    bulkTagIndividual: [],
    bulkTagCommon: [],
    bulkTagRemove: [],
    bulkTagAdd: [],

    bagbunker: Ember.inject.controller(),
    config: Ember.inject.service(),

    showfiltersInitial: Ember.computed('filter', function () {
        return !!this.get('filter').length;
    }),

    isFilterSet: Ember.computed('filterJSON', function() {
        return this.get('filterJSON').length === 2 ? true : undefined;
    }),

    isFilterApplied: Ember.computed('filter', 'filterB64', function() {
        return this.get('filter')===this.get('filterB64') ? true : undefined;
    }),

    updateFilter: Ember.on('init', Ember.observer('filter', function() {
        const filter = this.get('filter');
        if (!filter) {
            return;
        }
        this.set('filterObj', JSON.parse(atob(filter)));
    })),

    isNothingChecked: Ember.computed('checked.@each.checked', function() {
        return !this.get('checked').filterBy('checked').length;
    }),

    bulkTagIndividualMerged: Ember.computed(
        'bulkTagIndividual.[]',
        'bulkTagRemove.[]',
        'bulkTagAdd.[]',
    function() {
        const bti = this.get('bulkTagIndividual');
        const btr = this.get('bulkTagRemove');
        const bta = this.get('bulkTagAdd');

        return bti
            .filter(e => !~btr.indexOf(e))
            .filter(e => !~bta.indexOf(e));
    }),

    bulkTagCommonMerged: Ember.computed(
        'bulkTagCommon.[]',
        'bulkTagRemove.[]',
        'bulkTagAdd.[]',
    function() {
        const btc = this.get('bulkTagCommon');
        const btr = this.get('bulkTagRemove');
        const bta = this.get('bulkTagAdd');

        return btc
            .filter(e => !~btr.indexOf(e))
            .concat(bta.filter(e => !~btc.indexOf(e)));
    }),

    tagsIndex: Ember.computed('model.listing', function() {
        const c0 = this.get('model.listing.rows.firstObject.columns');
        return c0.indexOf(c0.findBy('name', 'tags'));
    }),

    commentsIndex: Ember.computed('model.listing', function() {
        const c0 = this.get('model.listing.rows.firstObject.columns');
        return c0.indexOf(c0.findBy('name', 'comment_count'));
    }),

    actions: {
        updateJSON() {
            const filterObj = this.get('filterObj');
            this.set('filterJSON', JSON.stringify(filterObj, 0, 2));

            const filterJSON = JSON.stringify(filterObj);
            let filterB64;

            if (filterJSON !== '{}') {
                filterB64 = btoa(filterJSON);
            } else {
                filterB64 = '';
            }

            this.set('filterB64', filterB64);
            if (this.get('autoupdate')) {
                this.set('filter', filterB64);
            }
        },

        applyFilter() {
            this.set('filter', this.get('filterB64'));
        },

        resetFilters() {
            this.set('filterObj', {});
            this.set('filterB64', '');
            this.set('filter', '');
        },

        show(row) {
            this.transitionToRoute('set', row['id']);
        },

        showFilters() {
            Ember.$('.filter-collapse').collapse('toggle');
        },

        toggleSelecting() {
            this.toggleProperty('isSelecting');
        },

        bulkTag() {
            const rows = this.get('checked').filterBy('checked');
            const index = this.get('tagsIndex');

            const allTags = [];
            rows.forEach(row => {
                row.columns[index].value.forEach(tag => {
                    if (!~allTags.indexOf(tag)) {
                        allTags.push(tag);
                    }
                });
            });

            const tagIndividual = allTags.filter(tag => {
                return rows.some(row => {
                    return !~row.columns[index].value.indexOf(tag);
                });
            });

            const tagCommon = allTags.filter(tag => {
                return !~tagIndividual.indexOf(tag);
            });

            this.set('bulkTagIndividual', tagIndividual);
            this.set('bulkTagCommon', tagCommon);
            this.set('bulkTagRemove', []);
            this.set('bulkTagAdd', []);

            Ember.run.scheduleOnce('afterRender', () => {
                Ember.$('[data-toggle="tooltip"]').tooltip();
            });

            Ember.$('.modal-bulk-tagging').modal('show');
        },

        bulkComment() {
            this.set('bulkComment', '');
            Ember.$('.modal-bulk-commenting').modal('show');
        },

        bulkTagAdd(tag) {
            if (!~this.get('bulkTagCommon').indexOf(tag)) {
                this.get('bulkTagAdd').pushObject(tag);
            }
            this.get('bulkTagRemove').removeObject(tag);
            this.set('newTag', '');
        },

        bulkTagRemove(tag) {
            this.get('bulkTagRemove').pushObject(tag);
            this.get('bulkTagAdd').removeObject(tag);
            this.set('newTag', '');
        },

        bulkTagUnqueue(tag) {
            this.get('bulkTagAdd').removeObject(tag);
            this.get('bulkTagRemove').removeObject(tag);
        },

        bulkTagApply() {
            const app = this.get('application');
            const rows = this.get('checked').filterBy('checked');
            const index = this.get('tagsIndex');

            function execTag(route, fileset, label) {
                const data = {
                    contentType : 'application/json',
                    data: JSON.stringify({
                        fileset_id: fileset,
                        tag_label: label
                    }),
                    type: 'POST'
                };
                return app.api(route, data);
            }

            const adds = this.get('bulkTagAdd');
            const removes = this.get('bulkTagRemove');

            let p = Ember.RSVP.Promise.resolve();

            rows.forEach((row, i) => {
                const tags = row.columns[index].value;

                adds.forEach(tag => {
                    if (!~tags.indexOf(tag)) {
                        p = p.then(() => {
                            this.set('bulkTagBeingSaved', rows.length-i);
                            return execTag('/marv/api/_tag', row.id, tag)
                                .then(() => tags.pushObject(tag));
                        });
                    }
                });
                removes.forEach(tag => {
                    if (~tags.indexOf(tag)) {
                        p = p.then(() => {
                            this.set('bulkTagBeingSaved', rows.length-i);
                            return execTag('/marv/api/_untag', row.id, tag)
                                .then(() => tags.removeObject(tag));
                        });
                    }
                });
            });

            return p.then(() => {
                Ember.$('.modal-bulk-tagging').modal('hide');

                // TODO: this is broken for some reason
                //this.notifyPropertyChange('model.listing');
                const listing = this.get('model.listing');
                this.set('model.listing', {
                    rows: listing.rows,
                    sort: listing.sort,
                    ascending: listing.ascending
                });
            });
        },

        async bulkCommentApply() {
            const mrows = this.get('model.listing.rows');
            const rows = this.get('checked').filterBy('checked');
            const user = this.get('session.user');
            const index = this.get('commentsIndex');

            const text = this.get('bulkComment');

            for (let row of rows) {
                this.set(
                    'bulkCommentBeingSaved',
                    rows.length-rows.indexOf(row)
                );
                const fileset = await this.store.find('fileset', row.id);
                await this.store.createRecord('comment', {
                    text: text,
                    author: user,
                    fileset: fileset
                }).save();
                mrows.findBy('id', row.id).columns[index].value++;
            }
            Ember.$('.modal-bulk-commenting').modal('hide');
            // TODO: this is broken for some reason
            //this.notifyPropertyChange('model.listing');
            const listing = this.get('model.listing');
            this.set('model.listing', {
                rows: listing.rows,
                sort: listing.sort,
                ascending: listing.ascending
            });
        },

        async downloadList(mapper) {
            const ids = this.get('checked').filterBy('checked').getEach('id');
            const filesets = await this.store.findByIds('fileset', ids);

            let files = [];
            for (let fileset of filesets) {
                const nfiles = await fileset.get('files');
                files = files.concat(nfiles.toArray().map(mapper));
            }

            const a = document.createElement("a");
            const blob = new Blob([files.join('\n')], {type: "text/plain"});
            const url = window.URL.createObjectURL(blob);
            document.body.appendChild(a);
            a.download = "files.txt";
            a.href = url;
            a.click();
            Ember.run.next(() => {
                a.remove();
                window.URL.revokeObjectURL(url);
            });
        },

        downloadFileList() {
            this.send('downloadList', r => {
                return `file://${r.get('fileset.dirpath')}/${r.get('name')}`;
            });
        },

        downloadUrlList() {
            // window.location.origin would be preferred
            const l = window.location;
            const host = l.protocol + '//' + l.hostname + ':' + l.port;

            this.send('downloadList', r => {
                return host + '/marv/download/' + r.get('md5');
            });
        },

        checked(checked) {
            this.set('checked', checked);
        }
    }
});
