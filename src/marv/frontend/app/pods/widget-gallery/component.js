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
    classNames: ['gallery'],
    index: 0,

    image: Ember.computed('index', function() {
        return this.get('model').images[this.get('index')];
    }),

    oneindex: Ember.computed('index', function() {
        return this.get('index')+1;
    }),

    actions: {
        setIndex(index) {
            if (index === '-1') {
                if (this.get('index') === 0) {
                    return;
                }
                this.decrementProperty('index');
            } else if (index === '+1') {
                if (this.get('index') === this.get('model.images.length')-1) {
                    return;
                }
                this.incrementProperty('index');
            } else {
                this.set('index', index);
            }
            // XXX: also scrolls vertically in some weird way
            // this.$().find('li').eq(this.get('index'))[0].scrollIntoView();
            this.sendAction('setIndex', this.get('index'));
        }
    }
});
