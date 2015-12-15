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
import c3 from 'c3';

export default Ember.Component.extend({
    flushChart: Ember.observer('flush', function() {
        if (this.chart) {
            this.chart.flush();
        }
    }),

    updateChart: Ember.observer('model', function() {
        const model = this.get('model');
        if (!model) {
            return;
        }

        if (!this.chart) {
            model.bindto = '#' + this.get('elementId');
            this.chart = c3.generate(model);
        } else {
            if (model.axis) {
                if (model.axis.x) {
                    this.chart.internal.config.axis_x_tick_format =
                        model.axis.x.tick ?
                        model.axis.x.tick.format :
                        undefined;
                    this.chart.internal.config.axis_x_tick_values =
                        model.axis.x.tick ?
                        model.axis.x.tick.values :
                        undefined;
                }
                if (model.axis.y) {
                    this.chart.internal.config.axis_y_tick_format =
                        model.axis.y.tick ?
                        model.axis.y.tick.format :
                        undefined;
                    this.chart.internal.config.axis_y_tick_values =
                        model.axis.y.tick ?
                        model.axis.y.tick.values :
                        undefined;
                }

                const range = {
                    min: {},
                    max: {}
                };
                for (let key in model.axis) {
                    if (typeof model.axis[key].min === 'number') {
                        range.min[key] = model.axis[key].min;
                    }
                    if (typeof model.axis[key].max === 'number') {
                        range.max[key] = model.axis[key].max;
                    }
                }
                this.chart.axis.range(range);
            }
            if (model.data.groups) {
                this.chart.groups(model.data.groups);
            }

            this.chart.load(model.data);

        }
    }),

    createChart: Ember.on('didInsertElement', function() {
        this.updateChart();
    }),

    destroyChart: Ember.on('willClearRender', function() {
        if (this.chart) {
            this.chart.destroy();
        }
    })
});
