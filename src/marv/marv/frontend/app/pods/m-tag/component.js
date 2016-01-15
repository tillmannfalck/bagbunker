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
    classNames: ['m-tag'],

    tags: null,
    suggestions: null,
    search: '',

    disabled: Ember.computed('subset', 'suggestions.length', function() {
        return this.get('subset') && !this.get('suggestions.length');
    }),

    placeholder: Ember.computed('subset', 'suggestions.length', function() {
        return this.get('subset') && !this.get('suggestions.length') ?
            'There are no items' : undefined;
    }),

    trackFocusIn: Ember.on('focusIn', function() {
        this.set('focused', true);
    }),

    trackFocusOut: Ember.on('focusOut', function() {
        this.set('focused', false);
    }),

    supressMouseDownOnDropDown: Ember.on('mouseDown', function(evt) {
        if (evt.target.tagName === "INPUT") {
            return;
        }
        evt.stopPropagation();
        evt.preventDefault();
    }),

    results: Ember.computed('search', 'tags.length', 'suggestions.length',
    function() {
        var search = this.get('search'),
            subset = this.get('subset');
        if (!search && !subset) {
            return [];
        }

        var tags = this.get('tags'),
            regex = new RegExp(search);
        return this
            .get('suggestions')
            .filter(function(tag) { return !~tags.indexOf(tag); })
            .filter(function(tag) { return regex.test(tag); })
            .map(function(tag) {
                return Ember.Object.create({
                    tag: tag,
                    active: false
                });
            });
    }),

    resultsVisible: Ember.computed('results.length', 'focused', function() {
        return this.get('results.length') && this.get('focused');
    }),

    enforceSubset: Ember.observer('subset', 'search', function() {
        var subset = this.get('subset');
        if (subset) {
            var search = this.get('search'),
                results = this.get('results');

            if (!results.length && search.length) {
                this.set('search', search.substr(0, search.length-1));
            }
        }
    }),

    processKeyboard: Ember.on('keyDown', function(e) {
        if (e.keyCode === 38) {
            this.send('highlight', -1);
            e.stopPropagation();
            e.preventDefault();
        } else if (e.keyCode === 40) {
            this.send('highlight', 1);
            e.stopPropagation();
            e.preventDefault();
        } else if (e.keyCode === 13 || e.keyCode === 9) {
            var tags = this.get('tags'),
                results = this.get('results'),
                search = this.get('search').trim();
            this.set('search', '');
            var c = results.findBy('active', true);

            if (c) {
                tags.addObject(c.tag);
                this.sendAction("add", c.tag);
            } else if (search.length) {
                if (!this.get('subset') || results.findBy('tag', search)) {
                    tags.addObject(search);
                    this.sendAction("add", search);
                }
            } else if (e.keyCode === 9) {
                return;
            }

            e.stopPropagation();
            e.preventDefault();
        } else if (e.keyCode === 8) {
            if (this.get('search.length')) {
                return;
            }
            this.sendAction("remove", this.get('tags').popObject());
            e.stopPropagation();
            e.preventDefault();
        }
    }),

    actions: {
        add: function(item) {
            this.get('tags').addObject(item.tag);
            this.set('search', '');
            this.sendAction("add", item.tag);
        },

        remove: function(tag) {
            this.get('tags').removeObject(tag);
            this.sendAction("remove", tag);
        },

        highlight: function(diff) {
            var results = this.get('results');
            if (!results.length) {
                return;
            }
            var c = results.findBy('active', true);
            results.setEach('active', false);

            if (typeof diff === 'number') {
                var index = results.indexOf(c);
                index = (index + results.length + diff) % results.length;

                results[index].set('active', true);
            } else {
                diff.set('active', true);
            }
        },

        focus: function() {
            this.$().find('input').focus();
        }
    }
});
