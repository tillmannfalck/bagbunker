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
        const roadmap = L.tileLayer('http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 22,
            maxNativeZoom: 19
        });
        const esri = L.tileLayer('http://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            attribution: '© <a href="http://www.esri.com/">Esri</a> i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
            maxZoom: 22,
            maxNativeZoom: 18
        });
        const trajectories = L.geoJson([], {
            style(feature) {
                return feature.properties.style || {};
            }
        });
        const map = L.map(this.$().find('.map')[0], {
            layers: [roadmap, trajectories],
            zoom: 16,
            minZoom: 0,
            maxZoom: 22,
            maxBounds: L.LatLngBounds(L.latLng([75,-180]), L.latLng([-75, 180]))
        });
        L.control.layers({'Roadmap': roadmap, 'Satellite': esri}, {'Trajectories': trajectories}).addTo(map);
        this.set('map', map);
        this.set('trajectories', trajectories);
        this.onModelChange();
    }),

    onModelChange: Ember.observer('model', function() {
        const trajectories = this.get('trajectories');
        if (!trajectories) {
            return;
        }
        trajectories.clearLayers();
        trajectories.addData(this.get('model.geoJSON') || []);

        const bounds = trajectories.getBounds();
        if (bounds.isValid()) {
            this.get('map').fitBounds(bounds, {
                padding: [100, 100],
                maxZoom: 18
            });
        }
    })
});
