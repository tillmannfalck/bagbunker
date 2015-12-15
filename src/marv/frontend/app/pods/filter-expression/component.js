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

export default Ember.Component.extend({
    classNames: ['filter-expression'],

    housekeeping: Ember.observer(
        'model.or.@each.{and,or,op}',
        'model.and.@each.{and,or,op}',
    function() {
        var model = this.get('model');

        var key = model.and ? 'and' : model.or ? 'or' : '';

        if (key) {
            var list = model[key],
                empties = list
                .filterBy('and', undefined)
                .filterBy('or', undefined)
                .filterBy('op', undefined);
            list.removeObjects(empties);
            if (list.get('length') === 1) {
                var item = list[0];
                Ember.setProperties(model, item);
                if (!item[key]) {
                    Ember.set(model, key, undefined);
                }
            }
        }
    }),

    notifyUpdate: Ember.observer("model.{and,or,name,op,val}", function() {
        this.sendAction('filterUpdated');
    }),

    actions: {
        initialize: function() {
            var model = this.get('model');
            Ember.setProperties(model, {
                name: '',
                op: ' ',
                val: '',
                _deleted: undefined
            });
        },
        convert: function(op) {
            var model = this.get('model'),
                child = Ember.copy(model);

            Ember.set(model, op, [ child, {
                name: '',
                op: ' ',
                val: ''
            } ]);

            Ember.setProperties(model, {
                    name: undefined,
                    op: undefined,
                    val: undefined
            });
        },

        add: function(filters) {
            filters.pushObject({
                name: '',
                op: ' ',
                val: ''
            });
        },

        remove: function(model) {
            Ember.setProperties(model, {
                and: undefined,
                or: undefined,
                name: undefined,
                op: undefined,
                val: undefined
            });
        },

        filterUpdated: function() {
            this.sendAction('filterUpdated');
        }
    }
});
