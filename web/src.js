// Written by Richard Christopher, Copyright 2026 NeoTec Digital
import App from "./app.js";

document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('canvas-container');
    const app = new App(container);
    app.init();
});
