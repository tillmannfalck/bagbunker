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
    classNames: ['form-horizontal'],

    fields: Ember.computed('filters', function() {
        var model = this.get('model'),
            filters = this.get('filters');

        // Filter fields are nicely nested with title. For now just flatten.
        return filters.reduce(function(acc, filter) {
            return acc.concat(filter.inputs.map(function(field) {
                return {
                    key: field.key,
                    title: field.title,
                    operators: field.operators,
                    value_type: field.value_type,
                    constraints: field.constraints,
                    error: null,

                    op: model[field.key] ? model[field.key].op : field.operators[0],
                    val: model[field.key] ? model[field.key].val : ''
                };
            }));
        }, []);
    }),

    housekeeping: Ember.observer('fields.@each.{op,val}', function() {
        var model = this.get('model');

        this.get('fields').forEach(function(field) {
            if (field.val != null) {
                model[field.key] = {
                    op: field.op,
                    val: field.val
                };
            } else {
                delete model[field.key];
            }
        });

        this.sendAction('filterUpdated');
    })

});
