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
import moment from 'moment';
import datetimepicker from 'eonasdan-bootstrap-datetimepicker'; //eslint-disable-line no-unused-vars

export default Ember.Component.extend({
    format: 'MMMM Do YYYY, HH:mm:ss',

    initShadow: Ember.on('init', function() {
        var value = this.get('value');
        if (value) {
            this.set('shadow', moment(value).format(this.format));
        }
    }),

    initElement: Ember.on('didInsertElement', function() {
        this.$('input').datetimepicker({
            showClear: true,
            showClose: true,
            useCurrent: false,
            format: this.format
        });
    }),

    updateValue: Ember.observer('shadow', function() {
        var shadow = this.get('shadow');
        if (shadow) {
            this.set('value', +moment(this.get('shadow'), this.format));
        } else {
            this.set('value', '');
        }
    })
});
