// Written by Richard Christopher, Copyright 2026 NeoTec Digital
import { GUI } from "https://unpkg.com/three@0.112/examples/jsm/libs/dat.gui.module.js";
import Topical from "./topical.js";

export default class Controller {
    constructor(engine) {
        this.engine = engine;
        this.gui = new GUI();

        this.params = {
            particlesPerType: 1000,
            globalAttraction: 0.0,
            globalRepulsion: 0.0,
            baseAttractions: {
                sameType: 0.2,
                orthogonal: 0.4,
                diagonal: 0.1,
                polar: -0.2
            },
            baseRepulsions: {
                sameType: 0.3,
                orthogonal: 0.0,
                diagonal: 0.0,
                polar: 0.4
            },
            typeMatrix: this.initializeTypeMatrix(),
            particleTypes: {
                a: {
                    color: "#00FF00",
                    attraction: { sameType: 0.0, orthogonal: 0.75, diagonal: 0.35, polar: 0.0 },
                    repulsion: { sameType: 1.0, orthogonal: 0.0, diagonal: 0.0, polar: 0.1 }
                },
                b: {
                    color: "#FF0000",
                    attraction: { sameType: 0.0, orthogonal: 0.75, diagonal: 0.35, polar: 0.0 },
                    repulsion: { sameType: 1.0, orthogonal: 0.0, diagonal: 0.0, polar: 0.1 }
                },
                c: {
                    color: "#0000FF",
                    attraction: { sameType: 0.0, orthogonal: 0.75, diagonal: 0.35, polar: 0.0 },
                    repulsion: { sameType: 1.0, orthogonal: 0.0, diagonal: 0.0, polar: 0.1 }
                },
                d: {
                    color: "#FFFF00",
                    attraction: { sameType: 0.0, orthogonal: 0.75, diagonal: 0.35, polar: 0.0 },
                    repulsion: { sameType: 1.0, orthogonal: 0.0, diagonal: 0.0, polar: 0.1 }
                },
                e: {
                    color: "#FF00FF",
                    attraction: { sameType: 0.0, orthogonal: 0.75, diagonal: 0.35, polar: 0.0 },
                    repulsion: { sameType: 1.0, orthogonal: 0.0, diagonal: 0.0, polar: 0.1 }
                },
                f: {
                    color: "#00FFFF",
                    attraction: { sameType: 0.0, orthogonal: 0.75, diagonal: 0.35, polar: 0.0 },
                    repulsion: { sameType: 1.0, orthogonal: 0.0, diagonal: 0.0, polar: 0.1 }
                },
                g: {
                    color: "#FFFFFF",
                    attraction: { sameType: 0.0, orthogonal: 0.75, diagonal: 0.35, polar: 0.0 },
                    repulsion: { sameType: 1.0, orthogonal: 0.0, diagonal: 0.0, polar: 0.1 }
                },
                h: {
                    color: "#FF8800",
                    attraction: { sameType: 0.0, orthogonal: 0.75, diagonal: 0.35, polar: 0.0 },
                    repulsion: { sameType: 1.0, orthogonal: 0.0, diagonal: 0.0, polar: 0.1 }
                }
            }
        };

        this.topical = new Topical(this.params);
        this.relationshipGrid = [];
        this.selectedType = 'a';
        this.biasPanel = null;
        this.matrixPanel = null;
        this.setupGUI();
    }

    initializeTypeMatrix() {
        const types = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
        const matrix = {};

        types.forEach(typeA => {
            matrix[typeA] = {};
            types.forEach(typeB => {
                matrix[typeA][typeB] = {
                    attraction: 0.0,
                    repulsion: 0.0
                };
            });
        });

        return matrix;
    }

    setupGUI() {
        const particleSystemFolder = this.gui.addFolder('Core Settings');
        particleSystemFolder.add(this.params, 'particlesPerType', 0, 2500).step(1)
            .onChange(() => {
                this.engine.particleSystem.init();
                this.topical.updateFromParams(this.params);
            });

        particleSystemFolder.add(this.params, 'globalAttraction', -1, 1).step(0.01)
            .name('Global Attraction')
            .onChange(() => {
                this.topical.updateFromParams(this.params);
                this.engine.particleSystem.updateFromController();
            });

        particleSystemFolder.add(this.params, 'globalRepulsion', -1, 1).step(0.01)
            .name('Global Repulsion')
            .onChange(() => {
                this.topical.updateFromParams(this.params);
                this.engine.particleSystem.updateFromController();
            });

        const attractionFolder = this.gui.addFolder('Attraction Settings');
        const repulsionFolder = this.gui.addFolder('Repulsion Settings');

        const addSliders = (folder, propObj, name) => {
            folder.add(propObj, 'sameType', -1, 1).step(0.01)
                .name('Same Type')
                .onChange(() => {
                    this.topical.updateFromParams(this.params);
                    this.engine.particleSystem.updateFromController();
                });

            folder.add(propObj, 'orthogonal', -1, 1).step(0.01)
                .name('Adjacent')
                .onChange(() => {
                    this.topical.updateFromParams(this.params);
                    this.engine.particleSystem.updateFromController();
                });

            folder.add(propObj, 'diagonal', -1, 1).step(0.01)
                .name('Diagonal')
                .onChange(() => {
                    this.topical.updateFromParams(this.params);
                    this.engine.particleSystem.updateFromController();
                });

            folder.add(propObj, 'polar', -1, 1).step(0.01)
                .name('Polar')
                .onChange(() => {
                    this.topical.updateFromParams(this.params);
                    this.engine.particleSystem.updateFromController();
                });
        };

        addSliders(attractionFolder, this.params.baseAttractions, 'Attraction');
        addSliders(repulsionFolder, this.params.baseRepulsions, 'Repulsion');

        // Wire the existing reset() to a GUI button.
        this.gui.add(this, 'reset').name('Reset');

        this.setup3DCubeVisualization();
        this.setupBiasControls();
        this.setupMatrixControls();
    }

    setup3DCubeVisualization() {
        const cubeContainer = document.createElement('div');
        cubeContainer.style.position = 'relative';
        cubeContainer.style.width = '280px';
        cubeContainer.style.height = '280px';
        cubeContainer.style.margin = '10px auto';
        cubeContainer.style.perspective = '800px';

        this.cube = document.createElement('div');
        this.cube.style.position = 'absolute';
        this.cube.style.width = '100%';
        this.cube.style.height = '100%';
        this.cube.style.transformStyle = 'preserve-3d';
        this.cube.style.transform = 'rotateX(20deg) rotateY(30deg)';

        // Set up mouse rotation
        let isDragging = false;
        let lastMouseX = 0;
        let lastMouseY = 0;
        let rotateX = 20;
        let rotateY = 30;

        cubeContainer.addEventListener('mousedown', (e) => {
            isDragging = true;
            lastMouseX = e.clientX;
            lastMouseY = e.clientY;
            e.preventDefault();
        });

        document.addEventListener('mousemove', (e) => {
            if (isDragging) {
                const deltaX = e.clientX - lastMouseX;
                const deltaY = e.clientY - lastMouseY;

                rotateY += deltaX * 0.5;
                rotateX -= deltaY * 0.5;

                rotateX = Math.max(-60, Math.min(60, rotateX));

                this.cube.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;

                // Update all node billboards to face the camera
                document.querySelectorAll('.node-content').forEach(content => {
                    content.style.transform = `rotateY(${-rotateY}deg) rotateX(${-rotateX}deg)`;
                });

                lastMouseX = e.clientX;
                lastMouseY = e.clientY;
            }
        });

        document.addEventListener('mouseup', () => {
            isDragging = false;
        });

        // Create nodes with proper 3D coordinates aligned with bit positions
        const nodePositions = {
            a: {x: -1, y: -1, z: -1},  // 000
            b: {x: 1, y: -1, z: -1},  // 100
            c: {x: -1, y: 1, z: -1},  // 010
            d: {x: 1, y: 1, z: -1},  // 110
            e: {x: -1, y: -1, z: 1},  // 001
            f: {x: 1, y: -1, z: 1},  // 101
            g: {x: -1, y: 1, z: 1},  // 011
            h: {x: 1, y: 1, z: 1}   // 111
        };

        // Generate connections based on fixed relationship definitions
        const connections = [];

        // Define relationships according to user specification
        const relationshipMap = {
            orthogonal: ['ab', 'ac', 'bd', 'cd', 'ae', 'bf', 'cg', 'dh', 'ef', 'eg', 'gh', 'fh'],
            diagonal: ['ad', 'af', 'ag', 'bc', 'be', 'bh', 'ce', 'ch', 'df', 'dg', 'eh', 'fg'],
            polar: ['ah', 'bg', 'cf', 'de']
        };

        Object.entries(relationshipMap).forEach(([relType, pairs]) => {
            pairs.forEach(pair => {
                const from = pair[0].toLowerCase();
                const to = pair[1].toLowerCase();

                connections.push({
                    from,
                    to,
                    type: relType,
                    posA: nodePositions[from],
                    posB: nodePositions[to]
                });
            });
        });

        // Store node elements for later reference
        this.nodeElements = {};

        // Create connection container
        const connectionsContainer = document.createElement('div');
        connectionsContainer.className = 'connections-container';
        connectionsContainer.style.position = 'absolute';
        connectionsContainer.style.width = '100%';
        connectionsContainer.style.height = '100%';
        connectionsContainer.style.transformStyle = 'preserve-3d';
        this.cube.appendChild(connectionsContainer);

        // Create all nodes first
        Object.entries(nodePositions).forEach(([type, pos]) => {
            const node = this.createCubeNode(type, pos);
            this.nodeElements[type] = node;
            this.cube.appendChild(node);
        });

        // Create all connections
        connections.forEach(conn => {
            const connection = document.createElement('div');
            connection.className = 'connection';
            connection.dataset.connection = `${conn.from}-${conn.to}`;
            connection.dataset.relationshipType = conn.type;
            connection.style.position = 'absolute';
            connection.style.transformStyle = 'preserve-3d';

            const posA = conn.posA;
            const posB = conn.posB;
            const scale = 60;
            const center = 140;

            // Calculate midpoint for the connection
            const midX = (posA.x + posB.x) / 2 * scale + center;
            const midY = (posA.y + posB.y) / 2 * scale + center;
            const midZ = (posA.z + posB.z) / 2 * scale;

            connection.style.left = `${midX}px`;
            connection.style.top = `${midY}px`;

            // Calculate distance and rotation
            const dx = posB.x - posA.x;
            const dy = posB.y - posA.y;
            const dz = posB.z - posA.z;

            const length = Math.sqrt(dx*dx + dy*dy + dz*dz) * scale;

            // Create cylinder instead of line
            const cylinder = document.createElement('div');
            cylinder.className = 'connection-cylinder';
            cylinder.style.position = 'absolute';
            cylinder.style.width = `${length}px`;
            cylinder.style.height = '6px';
            cylinder.style.borderRadius = '3px';
            cylinder.style.backgroundColor = '#FFFFFF';
            cylinder.style.transformOrigin = 'left center';
            cylinder.style.left = '0';
            cylinder.style.top = '-3px';

            // Calculate rotations
            const yaw = Math.atan2(dy, dx) * 180 / Math.PI;
            const pitch = Math.atan2(dz, Math.sqrt(dx*dx + dy*dy)) * 180 / Math.PI;

            // Create multiple cylinder segments to give a 3D appearance from all angles
            for (let i = 0; i < 4; i++) {
                const segment = cylinder.cloneNode();
                segment.style.transform = `rotateZ(${yaw}deg) rotateY(${pitch}deg) rotateX(${i * 45}deg) translateX(-50%)`;
                connection.appendChild(segment);
            }

            connection.style.transform = `translateZ(${midZ}px)`;
            connectionsContainer.appendChild(connection);
        });

        cubeContainer.appendChild(this.cube);
        this.gui.__ul.appendChild(cubeContainer);

        this.updateCubeConnections();
        this.highlightSelectedNode();
        this.updateSelectedTypeIndicator();
    }

    createCubeNode(type, pos) {
        const scale = 60;
        const center = 140;
        const size = 20;
        const halfSize = size / 2;

        // Create outer node container that handles 3D positioning
        const node = document.createElement('div');
        node.style.position = 'absolute';
        node.style.width = `${size}px`;
        node.style.height = `${size}px`;
        node.style.transformStyle = 'preserve-3d';
        node.style.transform = `translate3d(${pos.x * scale + center - halfSize}px, ${pos.y * scale + center - halfSize}px, ${pos.z * scale}px)`;
        node.dataset.type = type;
        node.style.zIndex = '100'; // Put nodes in front

        // Create inner content that will rotate to face camera
        const nodeContent = document.createElement('div');
        nodeContent.className = 'node-content';
        nodeContent.style.position = 'absolute';
        nodeContent.style.width = '100%';
        nodeContent.style.height = '100%';
        nodeContent.style.borderRadius = '50%';
        nodeContent.style.backgroundColor = this.params.particleTypes[type].color;
        nodeContent.style.cursor = 'pointer';
        nodeContent.style.boxSizing = 'border-box';
        nodeContent.style.boxShadow = '0 0 10px rgba(0,0,0,0.3)';
        nodeContent.style.transform = 'rotateY(0deg) rotateX(0deg)'; // Initial billboard orientation
        nodeContent.style.transformStyle = 'preserve-3d';

        // Add a label inside the node
        const label = document.createElement('span');
        label.textContent = type.toUpperCase();
        label.style.position = 'absolute';
        label.style.top = '50%';
        label.style.left = '50%';
        label.style.transform = 'translate(-50%, -50%)';
        label.style.fontSize = '10px';
        label.style.fontWeight = 'bold';
        label.style.color = this.getContrastColor(this.params.particleTypes[type].color);

        nodeContent.appendChild(label);
        node.appendChild(nodeContent);

        node.addEventListener('click', () => {
            this.selectedType = type;
            this.updateBiasControls();
            this.updateCubeConnections();
            this.highlightSelectedNode();
        });

        // Remove the outline/border if there was one
        nodeContent.style.border = 'none';

        return node;
    }

    updateCubeConnections() {
        document.querySelectorAll('.connection-cylinder').forEach(cylinder => {
            const connection = cylinder.parentElement;
            if (!connection.dataset.connection) return;

            const [typeA, typeB] = connection.dataset.connection.split('-');

            // Get fresh attraction value from our corrected topical mapping
            const attraction = this.topical.getAttractionValue(typeA, typeB);

            // Blue for attraction, red for repulsion
            const hue = attraction > 0 ? 240 : 0;
            const thickness = Math.abs(attraction) * 5 + 3;

            cylinder.style.backgroundColor = `hsl(${hue}, 80%, 50%)`;
            cylinder.style.height = `${thickness}px`;
            cylinder.style.opacity = Math.abs(attraction) * 0.8 + 0.2;

            // Highlight connections to selected node
            if (typeA === this.selectedType || typeB === this.selectedType) {
                cylinder.style.boxShadow = `0 0 5px hsl(${hue}, 80%, 50%)`;
                cylinder.style.zIndex = '10';
            } else {
                cylinder.style.boxShadow = 'none';
                cylinder.style.zIndex = '1';
            }
        });
    }

    updateBiasControls() {
        if (this.biasPanel) {
            this.biasPanel.remove();
        }

        this.setupBiasControls();
    }

    setupBiasControls() {
        if (this.biasPanel) {
            this.biasPanel.remove();
        }

        // Remove any existing 'Type Biases' folder so repeated node clicks can
        // rebuild the panel without dat.gui throwing a duplicate-folder error.
        const existingBiasFolder = this.gui.__folders['Type Biases'];
        if (existingBiasFolder) {
            this.gui.removeFolder(existingBiasFolder);
        }

        const types = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
        const relationLabels = {
            sameType: 'Same Type',
            orthogonal: 'Orthogonal',
            diagonal: 'Diagonal',
            polar: 'Polar'
        };
        const biasFolder = this.gui.addFolder('Type Biases');

        this.biasPanel = document.createElement('div');
        this.biasPanel.className = 'bias-panel';

        types.forEach(type => {
            const typeFolder = biasFolder.addFolder(`Type ${type.toUpperCase()}`);

            // Color control
            typeFolder.addColor(this.params.particleTypes[type], 'color')
                .onChange(() => {
                    this.topical.updateFromParams(this.params);
                    this.engine.particleSystem.updateFromController();
                });

            // Attraction controls
            const attractionFolder = typeFolder.addFolder('Attraction');
            for (const relType of ['sameType', 'orthogonal', 'diagonal', 'polar']) {
                attractionFolder.add(this.params.particleTypes[type].attraction, relType, 0, 1).step(0.01)
                    .name(relationLabels[relType])
                    .onChange(() => {
                        this.topical.updateFromParams(this.params);
                        this.engine.particleSystem.updateFromController();
                    });
            }

            // Repulsion controls
            const repulsionFolder = typeFolder.addFolder('Repulsion');
            for (const relType of ['sameType', 'orthogonal', 'diagonal', 'polar']) {
                repulsionFolder.add(this.params.particleTypes[type].repulsion, relType, 0, 1).step(0.01)
                    .name(relationLabels[relType])
                    .onChange(() => {
                        this.topical.updateFromParams(this.params);
                        this.engine.particleSystem.updateFromController();
                    });
            }
        });

        biasFolder.__ul.appendChild(this.biasPanel);
    }

    updateSelectedTypeIndicator() {
        if (!this.biasPanel) return;

        const title = this.biasPanel.querySelector('div');
        if (!title) return;

        title.innerHTML = '';

        const nodeColor = document.createElement('span');
        nodeColor.style.display = 'inline-block';
        nodeColor.style.width = '20px';
        nodeColor.style.height = '20px';
        nodeColor.style.backgroundColor = this.params.particleTypes[this.selectedType].color;
        nodeColor.style.borderRadius = '50%';
        nodeColor.style.marginRight = '5px';
        nodeColor.style.verticalAlign = 'middle';

        title.appendChild(nodeColor);
        title.appendChild(document.createTextNode(`Node ${this.selectedType.toUpperCase()}`));
    }

    updateRelationships() {
        if (this.engine.particles) {
            this.engine.particles.updateFromController();
        }
    }

    getParticleTypeFromPosition(gridPosition) {
        return this.topical.getTypeFromPosition(gridPosition);
    }

    getAttractionValue(typeA, typeB) {
        return this.topical.getAttractionValue(typeA, typeB);
    }

    reset() {
        // Mutate the existing objects in place so the dat.gui sliders (bound to
        // these references) keep editing the live values that physics reads,
        // rather than orphaned copies.
        Object.assign(this.params.baseAttractions, {
            sameType: 0.7,
            orthogonal: 0.5,
            diagonal: 0.3,
            polar: 0.1
        });
        Object.values(this.params.particleTypes).forEach(type => {
            Object.assign(type.attraction, { sameType: 0, orthogonal: 0, diagonal: 0, polar: 0 });
            Object.assign(type.repulsion, { sameType: 1, orthogonal: 0, diagonal: 0, polar: 0 });
        });

        // Clear cached values, push the reset params into the physics snapshot,
        // then refresh every GUI controller (including subfolders) so the
        // sliders display the reset values and motion stays consistent.
        this.topical.updateFromParams(this.params);
        this.engine.particleSystem.updateFromController();
        this.gui.updateDisplay();
        this.updateCubeConnections();
        this.updateRelationships();
    }

    getRelationshipType(typeA, typeB) {
        return this.topical.getRelationshipType(typeA, typeB);
    }

    getBinaryPosition(type) {
        return this.topical.getBinaryPosition(type);
    }

    getContrastColor(color) {
        // Choose black or white text based on the perceived luminance of the
        // supplied hex color so labels stay legible on any node color.
        const hex = color.replace('#', '');
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return luminance > 0.5 ? '#000000' : '#FFFFFF';
    }

    highlightSelectedNode() {
        // Reset all nodes first
        Object.values(this.nodeElements).forEach(node => {
            const content = node.querySelector('.node-content');
            if (content) {
                content.style.boxShadow = '0 0 10px rgba(0,0,0,0.3)';
            }
        });

        // Highlight the selected node
        const selectedNode = this.nodeElements[this.selectedType];
        if (selectedNode) {
            const content = selectedNode.querySelector('.node-content');
            if (content) {
                content.style.boxShadow = '0 0 15px #fff, 0 0 10px #fff';
            }
        }
    }

    setupMatrixControls() {
        if (this.matrixPanel) {
            this.matrixPanel.remove();
        }

        const matrixFolder = this.gui.addFolder('Type Matrix');

        const types = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];

        this.matrixPanel = document.createElement('div');
        this.matrixPanel.className = 'matrix-panel';
        this.matrixPanel.style.padding = '10px';
        this.matrixPanel.style.maxHeight = '300px';
        this.matrixPanel.style.overflowY = 'auto';

        const table = document.createElement('table');
        table.style.width = '100%';
        table.style.borderCollapse = 'collapse';

        // Create header row
        const headerRow = document.createElement('tr');
        const emptyHeader = document.createElement('th');
        headerRow.appendChild(emptyHeader);

        types.forEach(type => {
            const th = document.createElement('th');
            th.textContent = type.toUpperCase();
            th.style.padding = '2px';
            th.style.backgroundColor = this.params.particleTypes[type].color;
            th.style.color = this.getContrastColor(this.params.particleTypes[type].color);
            headerRow.appendChild(th);
        });

        table.appendChild(headerRow);

        // Create rows for each type
        types.forEach(typeA => {
            const row = document.createElement('tr');

            // Add row header
            const rowHeader = document.createElement('th');
            rowHeader.textContent = typeA.toUpperCase();
            rowHeader.style.padding = '2px';
            rowHeader.style.backgroundColor = this.params.particleTypes[typeA].color;
            rowHeader.style.color = this.getContrastColor(this.params.particleTypes[typeA].color);
            row.appendChild(rowHeader);

            // Add cells for each relationship
            types.forEach(typeB => {
                const cell = document.createElement('td');
                cell.style.padding = '5px';
                cell.style.textAlign = 'center';
                cell.style.border = '1px solid #ccc';

                // Display relationship type
                const relationshipType = this.topical.getRelationshipType(typeA, typeB);
                const relationshipLabel = document.createElement('div');
                relationshipLabel.textContent = relationshipType;
                relationshipLabel.style.fontSize = '10px';
                relationshipLabel.style.opacity = '0.7';
                cell.appendChild(relationshipLabel);

                // Create container for the sliders
                const sliderContainer = document.createElement('div');
                sliderContainer.style.display = 'flex';
                sliderContainer.style.flexDirection = 'column';
                sliderContainer.style.gap = '3px';

                // Attraction slider
                const attractionContainer = document.createElement('div');
                const attractionLabel = document.createElement('span');
                attractionLabel.textContent = 'A:';
                attractionLabel.style.color = 'blue';
                attractionLabel.style.marginRight = '3px';
                attractionContainer.appendChild(attractionLabel);

                const attractionSlider = document.createElement('input');
                attractionSlider.type = 'range';
                attractionSlider.min = 0;
                attractionSlider.max = 1;
                attractionSlider.step = 0.05;
                attractionSlider.value = this.params.typeMatrix[typeA][typeB].attraction;
                attractionSlider.style.width = '80px';

                attractionSlider.addEventListener('input', (e) => {
                    this.params.typeMatrix[typeA][typeB].attraction = parseFloat(e.target.value);
                    this.topical.updateFromParams(this.params);
                    this.engine.particleSystem.updateFromController();
                });

                attractionContainer.appendChild(attractionSlider);

                // Repulsion slider
                const repulsionContainer = document.createElement('div');
                const repulsionLabel = document.createElement('span');
                repulsionLabel.textContent = 'R:';
                repulsionLabel.style.color = 'red';
                repulsionLabel.style.marginRight = '3px';
                repulsionContainer.appendChild(repulsionLabel);

                const repulsionSlider = document.createElement('input');
                repulsionSlider.type = 'range';
                repulsionSlider.min = 0;
                repulsionSlider.max = 1;
                repulsionSlider.step = 0.05;
                repulsionSlider.value = this.params.typeMatrix[typeA][typeB].repulsion;
                repulsionSlider.style.width = '80px';

                repulsionSlider.addEventListener('input', (e) => {
                    this.params.typeMatrix[typeA][typeB].repulsion = parseFloat(e.target.value);
                    this.topical.updateFromParams(this.params);
                    this.engine.particleSystem.updateFromController();
                });

                repulsionContainer.appendChild(repulsionSlider);

                sliderContainer.appendChild(attractionContainer);
                sliderContainer.appendChild(repulsionContainer);

                cell.appendChild(sliderContainer);
            });

            table.appendChild(row);
        });

        this.matrixPanel.appendChild(table);

        // Generate the 128 matrix folder sliders (8 x 8 types x {attraction,
        // repulsion}) with nested loops instead of hand-unrolling every entry.
        const relationKinds = ['attraction', 'repulsion'];
        types.forEach(typeA => {
            types.forEach(typeB => {
                relationKinds.forEach(kind => {
                    matrixFolder.add(this.params.typeMatrix[typeA][typeB], kind, 0, 1).step(0.01)
                        .name(`${typeA}${typeB} ${kind}`)
                        .onChange(() => {
                            this.topical.updateFromParams(this.params);
                            this.engine.particleSystem.updateFromController();
                        });
                });
            });
        });

        this.gui.__ul.appendChild(this.matrixPanel);
    }
}
