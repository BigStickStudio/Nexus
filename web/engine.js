// Written by Richard Christopher, Copyright 2026 NeoTec Digital
import * as THREE from "https://unpkg.com/three@0.112/build/three.module.js";
import { OrbitControls } from "https://unpkg.com/three@0.112/examples/jsm/controls/OrbitControls.js";

class Engine {
    constructor(container) {
        this.container = container;
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ antialias: true });

        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.container.appendChild(this.renderer.domElement);

        this.camera.position.z = 20;
        this.boundingBoxSize = 10;

        this.preRenderCallbacks = [];

        this.gridSize = 1;

        this.setupLights();
        this.createBoundingBox();
        this.setupEventListeners();

        this.animate = this.animate.bind(this);
        this.controls = null;
    }

    setupLights() {
        const ambientLight = new THREE.AmbientLight(0x404040);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(1, 1, 1);
        this.scene.add(directionalLight);
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(window.innerWidth, window.innerHeight);
        });
    }

    addPreRenderCallback(callback) {
        this.preRenderCallbacks.push(callback);
    }

    setupControls() {
        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = false;
        this.controls.minDistance = 1;
        this.controls.maxDistance = 20;

        this.addPreRenderCallback(() => {
            this.controls.update();
        });
    }

    animate() {
        requestAnimationFrame(this.animate);

        for (const callback of this.preRenderCallbacks) {
            callback();
        }

        if (this.particleSystem) {
            this.particleSystem.update();
        }

        this.renderer.render(this.scene, this.camera);
    }

    start() {
        this.setupControls();
        this.animate();
    }

    createBoundingBox() {
        const boxSize = 10;

        const geometry = new THREE.BoxGeometry(boxSize * 2, boxSize * 2, boxSize * 2);
        const material = new THREE.MeshBasicMaterial({
            color: 0x444444,
            wireframe: true,
            transparent: true,
            opacity: 0.1
        });

        const boundingBox = new THREE.Mesh(geometry, material);
        this.scene.add(boundingBox);
    }

    setParticleSystem(particleSystem) {
        this.particleSystem = particleSystem;
    }

    setupGPUParticleSystem(count) {
        // For really huge particle counts - use a custom shader
        const vertexShader = `
            attribute float size;
            attribute vec3 customColor;
            varying vec3 vColor;

            void main() {
                vColor = customColor;
                vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                gl_PointSize = size * (300.0 / -mvPosition.z);
                gl_Position = projectionMatrix * mvPosition;
            }
        `;

        const fragmentShader = `
            varying vec3 vColor;

            void main() {
                // Create circular point
                vec2 xy = gl_PointCoord.xy - vec2(0.5);
                float radius = dot(xy, xy);
                if (radius > 0.25) discard;

                // Apply soft edge
                float alpha = 1.0 - smoothstep(0.2, 0.25, radius);
                gl_FragColor = vec4(vColor, alpha);
            }
        `;

        return {
            vertexShader,
            fragmentShader,
            uniforms: {}
        };
    }
}

export default Engine;
