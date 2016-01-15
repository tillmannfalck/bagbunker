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

export default Ember.Service.extend({
    retrieve: Ember.on('init', function() {
        const app = this.container.lookup('controller:application');

        app.api('/marv/api/_login').then(res => {
            this.setProperties(res);
            if (res.id) {
                return app.store.findRecord('user', res.id);
            } else {
                this.set('user', null);
            }
        }).then(user => this.set('user', user));
    }),

    signin: function(username, password) {
        var app = this.container.lookup('controller:application'),
            _this = this;

        var data = {
            method: 'POST',
            data: {
                username: username,
                password: password
            }
        };

        return app.api('/marv/api/_login', data).then(function(res) {
            _this.setProperties(res);
            return res;
        });
    },

    signout: function() {
        var app = this.container.lookup('controller:application'),
            _this = this;

        return app.api('/marv/api/_logout').then(function(res) {
            _this.setProperties({
                id: null,
                username: null
            });
            return res;
        });
    }
});
