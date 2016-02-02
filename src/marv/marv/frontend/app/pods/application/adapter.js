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

import DS from 'ember-data';

export default DS.JSONAPIAdapter.extend({
    ajax(url, type, options) {
        if (options && options.data && options.data.filter) {
            const filters = [];
            const filter = options.data.filter;
            delete options.data.filter;

            for (let key in filter) {
                filters.push({
                    name: key,
                    op: 'in',
                    val: filter[key].split(',').map(i => parseInt(i,10))
                })
            }
            options.data['filter[objects]'] = JSON.stringify(filters);
        }
        return this._super(url, type, options);
    },

    coalesceFindRequests: true,

    headers: {
        'Content-Type': 'application/vnd.api+json'
    },

    pathForType: function(type) {
        const regularTypes = [
            'fileset',
            'file',
            'comment',
            'tag',
            'user'
        ];

        if (~regularTypes.indexOf(type)) {
            return '/marv/api/' + type;
        }
    },

    shouldBackgroundReloadRecord() {
        return false;
    }
});
