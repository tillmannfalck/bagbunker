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
import THREE from 'three.js';
import PLYLoader from '../../PLYLoader';
import TrackballControls from '../../TrackballControls';

export default Ember.Component.extend({
    classNames: ['widget-3dviewer'],
    w: 640,
    h: 480,

    //fixControls: Ember.observer('controlTrigger', function() {
    //    this.controls.handleResize();
    //}),

    dispose(obj) {
        if (obj !== null) {
            if (obj.children) {
                for (var i=0; i<obj.children.length; i++) {
                    this.dispose(obj.children[i]);
                }
            }
            if (obj.geometry) {
                obj.geometry.dispose();
                obj.geometry = undefined;
            }

            if (obj.material) {
                if (obj.material.materials) {
                    for (i=0; i<obj.material.materials.length; i++) {
                        obj.material.materials[i].dispose();
                    }
                }
                if (obj.material.map) {
                    obj.material.map.dispose();
                    obj.material.map = undefined;
                }
                obj.material.dispose();
                obj.material = undefined;
            }
            if (obj.texture) {
                obj.texture.dispose();
                obj.texture = undefined;
            }
            if (obj.dispose) {
                obj.dispose();
            }
        }
        obj = undefined;
    },

    removeModel: Ember.observer('model', function() {
        if (this.mesh) {
            this.scene.remove(this.mesh);
            this.scene.remove(this.helper);
            this.dispose(this.mesh);
            this.dispose(this.helper);
            this.mesh = null;
            this.helper = null;
            this.controls.reset();
            this.camera.lookAt(this.scene.position);
            this.wglrenderer.render(this.scene, this.camera);
        }
    }),

    replaceModel: Ember.observer('controlTrigger', function() {
        if (this.$()) {
            this.loadMesh();
        }
    }),

    createContext: Ember.on('init', function() {
        this.wglrenderer = new THREE.WebGLRenderer({antialias: true});
        this.wglrenderer.setClearColor(0xaaaaaa, 1);
        this.wglrenderer.setSize(this.w, this.h);
        this.wglrenderer.setPixelRatio(window.devicePixelRatio);

        this.scene = new THREE.Scene();
        this.scene.name = 'scene';

        this.camera = new THREE.PerspectiveCamera(45, this.w / this.h, 1, 2000);
        this.camera.position.z = 100;
        this.camera.name = 'camera';
        this.scene.add(this.camera);

        const ambient = new THREE.AmbientLight(0xffffff);
        ambient.name = 'ambient';
        this.scene.add(ambient);

        const floorTexture = new THREE.ImageUtils.loadTexture(
            'app/styles/images/floor.jpg'
        );
        floorTexture.name = 'floorTexture';
        floorTexture.minFilter = THREE.NearestFilter;
        const floorMaterial = new THREE.MeshBasicMaterial({
            map: floorTexture,
            side: THREE.DoubleSide
        });
        const floorGeometry = new THREE.PlaneGeometry(134, 100, 1, 1);
        floorGeometry.name = 'floorGeometry';
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.name = 'floor';
        floor.position.set(0, 0, -5);
        floor.receiveShadow = true;
        this.scene.add(floor);

        const grid = new THREE.GridHelper(200, 10);
        grid.name = 'grid';
        grid.setColors(0x0000ff, 0x808080);
        grid.position.set(0, 0, -5.1);
        grid.rotation.set(Math.PI/2, 0, 0);
        this.scene.add(grid);

        this.controls = new TrackballControls(
            this.camera,
            this.wglrenderer.domElement
        );
        this.controls.name = 'ctrls';
        this.controls.rotateSpeed = 7.5;
        this.controls.zoomSpeed = 5;
        this.controls.panSpeed = 2;
        this.controls.noZoom = false;
        this.controls.noPan = false;
        this.controls.staticMoving = true;
        this.controls.dynamicDampingFactor = 0.3;

        this.loadingManager = new THREE.LoadingManager();
        this.loadingManager.name = 'loadingManager';
        //this.loadingManager.onProgress = function (item, loaded, total) {
        //    console.log(item, loaded, total);
        //};
    }),

    loadMesh: Ember.on('didInsertElement', function() {
        cancelAnimationFrame(this.reqid);
        this.element.firstChild.appendChild(this.wglrenderer.domElement);

        if (this.get('model') && !this.mesh) {
            Ember.run.later(this, function() {
                this.set('loading', true);
                const loader = new PLYLoader(this.loadingManager);
                loader.load(this.get('model'), (geometry) => {
                    geometry.vertices.forEach(v => {
                        if (v.x === 0 && v.y === 0 && v.z === 0) {
                            v.x = geometry.vertices[0].x;
                            v.y = geometry.vertices[0].y;
                            v.z = geometry.vertices[0].z;
                        }
                    })
                    geometry.normalize();
                    geometry.name = 'geometry';

                    const material = new THREE.MeshBasicMaterial({
                        vertexColors: THREE.VertexColors
                    });
                    material.name = 'material';

                    const mesh = new THREE.Mesh(geometry, material);
                    mesh.name = 'mesh';
                    mesh.rotation.set(0, Math.PI, Math.PI);
                    mesh.scale.set(20, 20, 20);

                    this.mesh = mesh;
                    this.helper = new THREE.BoxHelper(mesh);
                    this.helper.name = 'helper';
                    this.scene.add(mesh);
                    this.scene.add(this.helper);
                    this.set('loading', false);
                });
            }, 1);
        }
        this.controls.handleResize();
        this.animate();
    }),

    destroyScene: Ember.on('willClearRender', function() {
        cancelAnimationFrame(this.reqid);
        this.element.firstChild.removeChild(this.wglrenderer.domElement);
        this.dispose(this.scene);
        this.dispose(this.controls);
        this.wglrenderer.dispose();
    }),

    animate: function() {
        this.controls.update();
        this.camera.lookAt(this.scene.position);
        this.wglrenderer.render(this.scene, this.camera);
        this.reqid = requestAnimationFrame(() => this.animate());
    },

    handleResetCamera: Ember.observer('resetCamera', function() {
        this.controls.reset();
    })
});
