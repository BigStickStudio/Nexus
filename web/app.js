// Written by Richard Christopher, Copyright 2026 NeoTec Digital
import * as THREE from "https://unpkg.com/three@0.112/build/three.module.js";
import Controller from "./controller.js";
import Engine from "./engine.js";
import Particles from "./particles.js";

export default class App extends Engine {
    constructor(container) {
        super(container);

        // Update settings for performance
        THREE.Cache.enabled = true;
        this.renderer.setPixelRatio(window.devicePixelRatio > 1 ? 2 : 1);

        // Build the controller first so the particle system is initialized
        // exactly once, at the correct size (particlesPerType * 8). The legacy
        // sequence created it at 1000, grew it to 10000, then re-initialized to
        // 8000; passing the controller into the constructor initializes once.
        this.controller = new Controller(this);
        this.particleSystem = new Particles(this.scene, this.controller);
        this.particleSystem.setController(this.controller);
        this.setParticleSystem(this.particleSystem);

        // Add performance monitor
        this.setupPerformanceMonitor();
    }

    setupPerformanceMonitor() {
        // Simple FPS counter
        const fpsDisplay = document.createElement('div');
        fpsDisplay.style.position = 'absolute';
        fpsDisplay.style.top = '10px';
        fpsDisplay.style.right = '10px';
        fpsDisplay.style.color = 'white';
        fpsDisplay.style.fontFamily = 'monospace';
        fpsDisplay.style.padding = '5px';
        fpsDisplay.style.backgroundColor = 'rgba(0,0,0,0.5)';
        document.body.appendChild(fpsDisplay);

        let lastTime = performance.now();
        let frames = 0;

        this.addPreRenderCallback(() => {
            frames++;
            const now = performance.now();
            if (now - lastTime > 1000) {
                const fps = Math.round(frames * 1000 / (now - lastTime));
                fpsDisplay.textContent = `FPS: ${fps} | Particles: ${this.particleSystem.positions.length/3}`;
                frames = 0;
                lastTime = now;
            }
        });
    }

    init() {
        this.start();
    }
}
