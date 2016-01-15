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
    initialize: Ember.on('init', function() {
        this.set('value', this.get('field.val'));
    }),

    regex: /^\s*([0-9.]+)\s*([kmgtpezy][b]?)?\s*$/i,
    units: [ 'b', 'k', 'm', 'g', 't', 'p', 'e', 'z', 'y' ],

    calculateSize: function(value) {
        if (value === '') {
            return '';
        } else {
            var parts = this.regex.exec(value);
            if (!parts || isNaN(parts[1])) {
                return NaN;
            } else {
                value = +parts[1];
                if (parts[2]) {
                    value *= Math.pow(2, 10*this.units.indexOf(
                                parts[2][0].toLowerCase()));
                }

                return Math.floor(value);
            }
        }
    },

    propagateChanges: Ember.observer('value', function() {
        var value = this.get('value');

        var size = this.calculateSize(value);

        if (size === '') {
            this.set('field.val', null);
            this.set('field.error', null);
            this.set('size', '');
        } else if (isNaN(size)) {
            this.set('field.val', null);
            this.set(
                'field.error',
                'Value must be a number and optional unit (e.g. MB)'
            );
            this.set('size', '');
        } else {
            this.set('field.val', value);
            this.set('field.error', null);
            this.set('size', size + ' bytes');
        }
    })
});
