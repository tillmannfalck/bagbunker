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
    content: null,
    selectedValue: null,

    didInitAttrs(/*attrs*/) {
        this._super(...arguments);
        const content = this.get('content');

        if (!content) {
            this.set('content', []);
        }

        if (content.length) {
            const selectedValue = this.get('selectedValue');
            if (!~content.indexOf(selectedValue)) {
                //this.set('selectedValue', content[0]);
                this.get('action')(content[0]);
            }
        }
    },

    didUpdate() {
        this.send('change');
    },

    actions: {
        change() {
            const changeAction = this.get('action');
            const selectedEl = this.$('select')[0];
            const selectedIndex = selectedEl.selectedIndex;
            const content = this.get('content');
            const selectedValue = content[selectedIndex];

            changeAction(selectedValue);
        }
    }
});
