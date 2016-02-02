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
    sanitize: Ember.on('init', function() {
        var colvalues = this.get('columns').getEach('key'),
            model = this.get('model');

        if (!~colvalues.indexOf(model.name)) {
            Ember.set(model, 'name', colvalues[0]);
        }

        if (!~this.operators.indexOf(model.op)) {
            Ember.set(model, 'op', this.operators[0]);
        }
    }),

    valid: Ember.computed('model.{name,op,val}', function() {
        var model = this.get('model');
        return model.name && model.op && model.val;
    }),

    operators: [
        '==',
        '!=',
        '>',
        '<',
        '>=',
        '<=',
        'in',
        'not_in',
        'is_null',
        'is_not_null',
        'like',
        'has',
        'any'
    ]
});
