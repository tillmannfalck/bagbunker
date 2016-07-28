/*
 * Copyright 2016 Ternaris, Munich, Germany
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
import L from 'leaflet';

L.Icon.Default.imagePath = '/bower_components/leaflet/dist/images';

export default Ember.Component.extend({
    classNames: ['widget-osm'],

    boot: Ember.on('didInsertElement', function() {
        const map = L.map(this.$().find('.map')[0], {
            minZoom: 0,
            maxZoom: 22,
            attributionControl: false,
            maxBounds: L.LatLngBounds(L.latLng([75,-180]), L.latLng([-75, 180]))
        });
        this.set('map', map);

        L.tileLayer(`${window.location.protocol}//{s}.osm.ternaris.com/mapbox-studio-osm-bright/{z}/{x}/{y}${L.Browser.retina ? '@2x' : ''}.png`, {
            maxZoom: 22
        }).addTo(map);

        const geo = L.geoJson([], {
            style(feature) {
                return feature.properties.style || {};
            }
        }).addTo(map);
        this.set('geo', geo);
        this.onModelChange();
    }),

    onModelChange: Ember.observer('model', function() {
        const geo = this.get('geo');
        if (!geo) {
            return;
        }
        geo.clearLayers();
        geo.addData(this.get('model.geoJSON') || []);

        const bounds = geo.getBounds();
        if (bounds.isValid()) {
            this.get('map').fitBounds(bounds, {
                padding: [100, 100]
            });
        }
    })
});
