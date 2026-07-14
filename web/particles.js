// Written by Richard Christopher, Copyright 2026 NeoTec Digital
import * as THREE from "https://unpkg.com/three@0.112/build/three.module.js";

export default class Particles {
    constructor(scene, controller = null) {
        this.scene = scene;
        this.controller = controller;
        this.particles = [];
        this.particleCount = 0;

        // Use typed arrays for better performance
        this.positions = null;
        this.velocities = null;
        this.colors = null;
        this.energies = null;
        this.types = null;
        this.typeIndices = null; // Store numeric type indices for faster comparison

        // For instanced rendering
        this.instancedMesh = null;
        this.dummy = new THREE.Object3D();

        // For spatial partitioning (optimized grid)
        this.grid = {};
        this.cellSize = 3.0; // Larger cell size for fewer checks

        // For GPU acceleration
        this.usePointCloud = true; // Use point cloud for massive particle counts
        this.pointCloudSystem = null;

        // Performance optimizations
        this.updateEveryNthParticle = 5; // Only update subset of particles each frame
        this.frameCount = 0;
        this.maxDistance = 5.0; // Maximum interaction distance
        this.maxDistanceSq = this.maxDistance * this.maxDistance;

        // Preallocated objects to prevent GC
        this._tempVector = new THREE.Vector3();
        this._tempColor = new THREE.Color();
        this._tempMatrix = new THREE.Matrix4();

        // Initialize immediately
        this.init();
    }

    init() {
        const totalParticles = this.controller ?
            this.controller.params.particlesPerType * 8 :
            1000; // Default to 1000 if no controller

        // Initialize typed arrays for better performance
        this.positions = new Float32Array(totalParticles * 3);
        this.velocities = new Float32Array(totalParticles * 3);
        this.colors = new Float32Array(totalParticles * 3);
        this.energies = new Float32Array(totalParticles);
        this.types = new Array(totalParticles);
        this.typeIndices = new Uint8Array(totalParticles);

        // Create particles
        for (let i = 0; i < totalParticles; i++) {
            const typeIndex = i % 8;
            const type = String.fromCharCode(97 + typeIndex);

            // Set positions
            const idx = i * 3;
            this.positions[idx] = (Math.random() - 0.5) * 10;
            this.positions[idx + 1] = (Math.random() - 0.5) * 10;
            this.positions[idx + 2] = (Math.random() - 0.5) * 10;

            // Set initial velocities
            this.velocities[idx] = (Math.random() - 0.5) * 0.02;
            this.velocities[idx + 1] = (Math.random() - 0.5) * 0.02;
            this.velocities[idx + 2] = (Math.random() - 0.5) * 0.02;

            // Set other properties
            this.types[i] = type;
            this.typeIndices[i] = typeIndex;
            this.energies[i] = 1.0;

            // Set colors
            if (this.controller?.params?.particleTypes) {
                const typeData = this.controller.params.particleTypes[type];
                if (typeData) {
                    const color = new THREE.Color(typeData.color);
                    this.colors[idx] = color.r;
                    this.colors[idx + 1] = color.g;
                    this.colors[idx + 2] = color.b;
                } else {
                    this.colors[idx] = 1;
                    this.colors[idx + 1] = 1;
                    this.colors[idx + 2] = 1;
                }
            } else {
                this.colors[idx] = (typeIndex % 3 === 0) ? 1 : 0.3;
                this.colors[idx + 1] = (typeIndex % 3 === 1) ? 1 : 0.3;
                this.colors[idx + 2] = (typeIndex % 3 === 2) ? 1 : 0.3;
            }
        }

        // Always use point cloud system
        this.initPointCloudSystem(totalParticles);

        // Initialize spatial grid
        this.updateSpatialGrid();
    }

    setParticleCount(count) {
        const currentCount = this.positions ? this.positions.length / 3 : 0;

        if (count === currentCount) return;

        if (count > currentCount) {
            // Create new particles
            if (!this.positions) {
                // Initialize arrays if they don't exist
                this.positions = new Float32Array(count * 3);
                this.velocities = new Float32Array(count * 3);
                this.colors = new Float32Array(count * 3);
                this.energies = new Float32Array(count);
                this.types = new Array(count);
                this.typeIndices = new Uint8Array(count);
            } else {
                // Expand arrays
                this.expandArraysIfNeeded(count);
            }

            // Fill with new particles
            for (let i = currentCount; i < count; i++) {
                const typeIndex = i % 8;
                const type = String.fromCharCode(97 + typeIndex);

                // Set default values
                const idx = i * 3;
                this.positions[idx] = (Math.random() - 0.5) * 5;
                this.positions[idx + 1] = (Math.random() - 0.5) * 5;
                this.positions[idx + 2] = (Math.random() - 0.5) * 5;

                this.velocities[idx] = (Math.random() - 0.5) * 0.02;
                this.velocities[idx + 1] = (Math.random() - 0.5) * 0.02;
                this.velocities[idx + 2] = (Math.random() - 0.5) * 0.02;

                this.types[i] = type;
                this.typeIndices[i] = typeIndex;

                if (this.controller?.params.particleTypes) {
                    const typeData = this.controller.params.particleTypes[type];
                    const color = new THREE.Color(typeData.color);
                    this.colors[idx] = color.r;
                    this.colors[idx + 1] = color.g;
                    this.colors[idx + 2] = color.b;
                } else {
                    this.colors[idx] = 1;
                    this.colors[idx + 1] = 1;
                    this.colors[idx + 2] = 1;
                }

                this.energies[i] = 1.0;
            }
        } else {
            // Reduce arrays
            const newPositions = new Float32Array(count * 3);
            const newVelocities = new Float32Array(count * 3);
            const newColors = new Float32Array(count * 3);
            const newEnergies = new Float32Array(count);
            const newTypes = new Array(count);
            const newTypeIndices = new Uint8Array(count);

            newPositions.set(this.positions.subarray(0, count * 3));
            newVelocities.set(this.velocities.subarray(0, count * 3));
            newColors.set(this.colors.subarray(0, count * 3));

            for (let i = 0; i < count; i++) {
                newTypes[i] = this.types[i];
                newTypeIndices[i] = this.typeIndices[i];
            }

            this.positions = newPositions;
            this.velocities = newVelocities;
            this.colors = newColors;
            this.energies = newEnergies;
            this.types = newTypes;
            this.typeIndices = newTypeIndices;
        }

        // Update point cloud with new arrays
        this.pointCloudSystem.geometry.setAttribute(
            'position',
            new THREE.BufferAttribute(this.positions, 3)
        );
        this.pointCloudSystem.geometry.setAttribute(
            'color',
            new THREE.BufferAttribute(this.colors, 3)
        );

        const sizes = new Float32Array(count);
        for (let i = 0; i < count; i++) {
            sizes[i] = 0.2 + this.energies[i] * 0.2;
        }
        this.pointCloudSystem.geometry.setAttribute(
            'size',
            new THREE.BufferAttribute(sizes, 1)
        );
    }

    initPointCloudSystem(count) {
        // Remove old point cloud if it exists
        if (this.pointCloudSystem) {
            this.scene.remove(this.pointCloudSystem);
        }

        // Create geometry with buffer attributes
        const geometry = new THREE.BufferGeometry();

        // Set positions
        geometry.setAttribute('position', new THREE.BufferAttribute(this.positions, 3));

        // Set colors
        geometry.setAttribute('color', new THREE.BufferAttribute(this.colors, 3));

        // Set sizes (based on energy)
        const sizes = new Float32Array(count);
        for (let i = 0; i < count; i++) {
            sizes[i] = 0.2 + this.energies[i] * 0.2;
        }
        geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

        // Create point material with better appearance
        const material = new THREE.PointsMaterial({
            size: 0.3,
            vertexColors: true,
            sizeAttenuation: true,
            transparent: true,
            opacity: 0.8,
            depthWrite: false
        });

        // Create points and add to scene
        this.pointCloudSystem = new THREE.Points(geometry, material);
        this.scene.add(this.pointCloudSystem);

        // Ensure scene has the point cloud
        console.log("Point cloud system initialized with", count, "particles");
    }

    updateSpatialGrid() {
        // Clear grid (reuse object to reduce GC)
        for (const key in this.grid) {
            delete this.grid[key];
        }

        // Add particles to grid
        const count = this.positions.length / 3;

        // Only update a subset of particles each frame for huge counts
        const start = (this.frameCount % this.updateEveryNthParticle) * Math.floor(count / this.updateEveryNthParticle);
        const end = Math.min(start + Math.floor(count / this.updateEveryNthParticle), count);

        for (let i = 0; i < count; i++) {
            const idx = i * 3;
            const cellX = Math.floor(this.positions[idx] / this.cellSize);
            const cellY = Math.floor(this.positions[idx + 1] / this.cellSize);
            const cellZ = Math.floor(this.positions[idx + 2] / this.cellSize);
            const cellKey = `${cellX},${cellY},${cellZ}`;

            if (!this.grid[cellKey]) {
                this.grid[cellKey] = [];
            }
            this.grid[cellKey].push(i);
        }
    }

    getNeighborIndices(index) {
        const idx = index * 3;
        const x = this.positions[idx];
        const y = this.positions[idx + 1];
        const z = this.positions[idx + 2];

        const cellX = Math.floor(x / this.cellSize);
        const cellY = Math.floor(y / this.cellSize);
        const cellZ = Math.floor(z / this.cellSize);

        const neighbors = [];

        // Only check current cell and immediate neighbors
        // (reduces neighbors check from 27 cells to 7 cells on average)
        const checkCells = [
            [cellX, cellY, cellZ],  // Current cell
            [cellX+1, cellY, cellZ], // Adjacent cells (selective)
            [cellX, cellY+1, cellZ],
            [cellX, cellY, cellZ+1],
            [cellX-1, cellY, cellZ],
            [cellX, cellY-1, cellZ],
            [cellX, cellY, cellZ-1]
        ];

        for (const [x, y, z] of checkCells) {
            const cellKey = `${x},${y},${z}`;
            if (this.grid[cellKey]) {
                // Only add up to 20 neighbors per cell to limit calculations
                const cellNeighbors = this.grid[cellKey];
                const maxNeighborsFromCell = Math.min(cellNeighbors.length, 20);
                for (let i = 0; i < maxNeighborsFromCell; i++) {
                    neighbors.push(cellNeighbors[i]);
                }
            }
        }

        return neighbors;
    }

    update() {
        this.frameCount++;

        // Update controller data
        if (this.controller?.topical) {
            const typeMatrix = this.controller.params.typeMatrix;
            const particleTypes = this.controller.params.particleTypes;
            const globalAttraction = this.controller.params.globalAttraction;
            const globalRepulsion = this.controller.params.globalRepulsion;
            this.scene.userData.particles = {
                typeMatrix, particleTypes, globalAttraction, globalRepulsion
            };
        }

        // Update spatial grid (staggered updates)
        if (this.frameCount % 3 === 0) {
            this.updateSpatialGrid();
        }

        // Process physics
        this.updateParticles();

        // Process transformations
        this.transformParticles();

        // Update rendering
        if (this.pointCloudSystem) {
            this.updatePointCloud();
        } else {
            console.warn("Point cloud system is null during update");
            this.initPointCloudSystem(this.positions.length / 3);
        }
    }

    updateParticles() {
        const { typeMatrix, particleTypes, globalAttraction, globalRepulsion } = this.scene.userData.particles || {};
        const boundaryLimit = 10;
        const particleCount = this.positions.length / 3;

        // Only process a subset of particles each frame
        const chunkSize = Math.ceil(particleCount / this.updateEveryNthParticle);
        const startIdx = (this.frameCount % this.updateEveryNthParticle) * chunkSize;
        const endIdx = Math.min(startIdx + chunkSize, particleCount);

        // Update number of particles if particle count changes in gui
        if (this.controller?.params) {
            const targetCount = this.controller.params.particlesPerType * 8;
            const currentCount = this.positions.length / 3;

            if (targetCount < currentCount) {
                // Remove particles
                const newSize = targetCount * 3;
                this.positions = this.positions.slice(0, newSize);
                this.velocities = this.velocities.slice(0, newSize);
                this.colors = this.colors.slice(0, newSize);
                this.energies = this.energies.slice(0, targetCount);
                this.types = this.types.slice(0, targetCount);
                this.typeIndices = this.typeIndices.slice(0, targetCount);

                // Update rendering
                this.pointCloudSystem.geometry.setAttribute(
                    'position',
                    new THREE.BufferAttribute(this.positions, 3)
                );
                this.pointCloudSystem.geometry.setAttribute(
                    'color',
                    new THREE.BufferAttribute(this.colors, 3)
                );

                const sizes = new Float32Array(targetCount);
                for (let i = 0; i < targetCount; i++) {
                    sizes[i] = 0.2 + this.energies[i] * 0.2;
                }
                this.pointCloudSystem.geometry.setAttribute(
                    'size',
                    new THREE.BufferAttribute(sizes, 1)
                );
            } else if (targetCount > currentCount) {
                // Add particles
                const particlesToAdd = targetCount - currentCount;

                // Expand arrays if needed
                this.expandArraysIfNeeded(targetCount);

                // Add new particles
                for (let i = 0; i < particlesToAdd; i++) {
                    this.createRandomParticle();
                }
            }
        }

        // Update positions of all particles
        for (let i = 0; i < particleCount; i++) {
            const idx = i * 3;

            // Update position
            this.positions[idx] += this.velocities[idx];
            this.positions[idx + 1] += this.velocities[idx + 1];
            this.positions[idx + 2] += this.velocities[idx + 2];

            // Boundary checks
            if (Math.abs(this.positions[idx]) > boundaryLimit) {
                this.velocities[idx] *= -1;
                this.positions[idx] = Math.sign(this.positions[idx]) * boundaryLimit;
            }
            if (Math.abs(this.positions[idx + 1]) > boundaryLimit) {
                this.velocities[idx + 1] *= -1;
                this.positions[idx + 1] = Math.sign(this.positions[idx + 1]) * boundaryLimit;
            }
            if (Math.abs(this.positions[idx + 2]) > boundaryLimit) {
                this.velocities[idx + 2] *= -1;
                this.positions[idx + 2] = Math.sign(this.positions[idx + 2]) * boundaryLimit;
            }

            // Dampen velocities
            this.velocities[idx] *= 0.98;
            this.velocities[idx + 1] *= 0.98;
            this.velocities[idx + 2] *= 0.98;
        }

        // Apply forces only to subset of particles each frame
        for (let i = startIdx; i < endIdx; i++) {
            const idx = i * 3;
            const type = this.types[i];

            // Apply forces from neighbors
            const neighbors = this.getNeighborIndices(i);

            for (const j of neighbors) {
                if (i === j) continue;

                const otherIdx = j * 3;

                // Calculate distance squared (avoid square root)
                const dx = this.positions[otherIdx] - this.positions[idx];
                const dy = this.positions[otherIdx + 1] - this.positions[idx + 1];
                const dz = this.positions[otherIdx + 2] - this.positions[idx + 2];
                const distSq = dx*dx + dy*dy + dz*dz;

                // Skip particles that are too far away
                if (distSq > this.maxDistanceSq) continue;

                const otherType = this.types[j];

                // Get relationship type
                const relationType = this.getRelationshipType(type, otherType);

                // Calculate attraction force
                let attractionStrength = globalAttraction || 0;

                // Add base attraction for relationship type
                if (this.controller?.params.baseAttractions) {
                    attractionStrength += this.controller.params.baseAttractions[relationType] || 0;
                }

                // Add type-specific attraction bias from particle type settings
                // (nested form particleTypes[type].attraction[relationType]).
                if (particleTypes && particleTypes[type] && particleTypes[type].attraction) {
                    attractionStrength += particleTypes[type].attraction[relationType] || 0;
                }

                // Add specific type-to-type attraction
                if (typeMatrix && typeMatrix[type] && typeMatrix[type][otherType]) {
                    attractionStrength += typeMatrix[type][otherType].attraction || 0;
                }

                // Calculate repulsion force
                let repulsionStrength = globalRepulsion || 0;

                // Add base repulsion for relationship type
                if (this.controller?.params.baseRepulsions) {
                    repulsionStrength += this.controller.params.baseRepulsions[relationType] || 0;
                }

                // Add type-specific repulsion bias from particle type settings
                // (nested form particleTypes[type].repulsion[relationType]).
                if (particleTypes && particleTypes[type] && particleTypes[type].repulsion) {
                    repulsionStrength += particleTypes[type].repulsion[relationType] || 0;
                }

                // Add specific type-to-type repulsion
                if (typeMatrix && typeMatrix[type] && typeMatrix[type][otherType]) {
                    repulsionStrength += typeMatrix[type][otherType].repulsion || 0;
                }

                // Calculate net force
                const invDist = 1 / Math.sqrt(distSq);
                const distanceFactor = 1 / (1 + distSq);

                // Attraction pulls particles together (positive force)
                const attractionForce = attractionStrength * distanceFactor * 0.05;

                // Repulsion pushes particles apart (negative force)
                // Repulsion is stronger at close distances
                const repulsionForce = repulsionStrength * distanceFactor * 0.1 * (1 / (distSq + 0.1));

                // Net force (positive = attraction, negative = repulsion)
                const netForce = attractionForce - repulsionForce;

                // Apply force
                this.velocities[idx] += dx * invDist * netForce;
                this.velocities[idx + 1] += dy * invDist * netForce;
                this.velocities[idx + 2] += dz * invDist * netForce;
            }

            // Speed limit
            const speedSq =
                this.velocities[idx] * this.velocities[idx] +
                this.velocities[idx + 1] * this.velocities[idx + 1] +
                this.velocities[idx + 2] * this.velocities[idx + 2];

            if (speedSq > 0.04) { // 0.2^2
                const speedFactor = 0.2 / Math.sqrt(speedSq);
                this.velocities[idx] *= speedFactor;
                this.velocities[idx + 1] *= speedFactor;
                this.velocities[idx + 2] *= speedFactor;
            }
        }
    }

    updatePointCloud() {
        if (!this.pointCloudSystem) {
            console.warn("Point cloud system is null during updatePointCloud");
            return;
        }

        // Make sure geometry and attributes exist
        if (!this.pointCloudSystem.geometry) {
            console.warn("Point cloud geometry is missing");
            return;
        }

        // Update positions in geometry
        if (this.pointCloudSystem.geometry.attributes.position) {
            this.pointCloudSystem.geometry.attributes.position.array = this.positions;
            this.pointCloudSystem.geometry.attributes.position.needsUpdate = true;
        }

        // Update colors in geometry
        if (this.pointCloudSystem.geometry.attributes.color) {
            this.pointCloudSystem.geometry.attributes.color.array = this.colors;
            this.pointCloudSystem.geometry.attributes.color.needsUpdate = true;
        }

        // Update sizes based on energy (only every few frames to save performance)
        if (this.pointCloudSystem.geometry.attributes.size && this.frameCount % 10 === 0) {
            const sizeAttr = this.pointCloudSystem.geometry.attributes.size;
            const count = Math.min(sizeAttr.array.length, this.energies.length);
            for (let i = 0; i < count; i++) {
                sizeAttr.array[i] = 0.2 + this.energies[i] * 0.2;
            }
            sizeAttr.needsUpdate = true;
        }
    }

    getRelationshipType(typeA, typeB) {
        if (typeA === typeB) return 'sameType';

        // Optimized - using type cache in controller if available
        if (this.controller?.topical) {
            return this.controller.topical.getRelationshipType(typeA, typeB);
        }

        // Fallback
        const aBits = this.getTypeBits(typeA);
        const bBits = this.getTypeBits(typeB);

        let diffCount = 0;
        for (let i = 0; i < 3; i++) {
            if (aBits[i] !== bBits[i]) diffCount++;
        }

        switch(diffCount) {
            case 1: return 'orthogonal';
            case 2: return 'diagonal';
            case 3: return 'polar';
            default: return 'sameType';
        }
    }

    getTypeBits(type) {
        if (this.controller?.topical) {
            return this.controller.topical.getTypeBits(type);
        }

        const bitMap = {
            a: [0, 0, 0], b: [1, 0, 0], c: [0, 1, 0], d: [1, 1, 0],
            e: [0, 0, 1], f: [1, 0, 1], g: [0, 1, 1], h: [1, 1, 1]
        };
        return bitMap[type] || [0, 0, 0];
    }

    getPositionForType(type) {
        const offsets = {
            a: [0,0,0], b: [1,0,0], c: [0,1,0], d: [1,1,0],
            e: [0,0,1], f: [1,0,1], g: [0,1,1], h: [1,1,1]
        };
        const base = offsets[type] || [0,0,0];

        return new THREE.Vector3(
            (base[0] + Math.random() - 0.5) * 0.9,
            (base[1] + Math.random() - 0.5) * 0.9,
            (base[2] + Math.random() - 0.5) * 0.9
        );
    }

    createRandomParticle() {
        const position = new THREE.Vector3(
            (Math.random() - 0.5) * 5,
            (Math.random() - 0.5) * 5,
            (Math.random() - 0.5) * 5
        );

        const gridPos = new THREE.Vector3(
            Math.floor(position.x + 0.5) % 2,
            Math.floor(position.y + 0.5) % 2,
            Math.floor(position.z + 0.5) % 2
        );

        const type = this.getParticleTypeFromPosition(gridPos);

        // Add to typed arrays
        const i = this.positions.length / 3;
        const idx = i * 3;

        // Set position
        this.positions[idx] = position.x;
        this.positions[idx + 1] = position.y;
        this.positions[idx + 2] = position.z;

        // Set velocity
        this.velocities[idx] = (Math.random() - 0.5) * 0.02;
        this.velocities[idx + 1] = (Math.random() - 0.5) * 0.02;
        this.velocities[idx + 2] = (Math.random() - 0.5) * 0.02;

        // Set type
        this.types[i] = type;
        this.typeIndices[i] = type.charCodeAt(0) - 97;

        // Set color
        if (this.controller?.params.particleTypes) {
            const typeData = this.controller.params.particleTypes[type];
            const color = new THREE.Color(typeData.color);
            this.colors[idx] = color.r;
            this.colors[idx + 1] = color.g;
            this.colors[idx + 2] = color.b;
        } else {
            this.colors[idx] = 1;
            this.colors[idx + 1] = 1;
            this.colors[idx + 2] = 1;
        }

        // Set energy
        this.energies[i] = 1.0;

        return i;
    }

    expandArraysIfNeeded(newSize) {
        const currentSize = this.positions.length / 3;

        if (newSize > currentSize) {
            // Create new expanded arrays
            const newPositions = new Float32Array(newSize * 3);
            const newVelocities = new Float32Array(newSize * 3);
            const newColors = new Float32Array(newSize * 3);
            const newEnergies = new Float32Array(newSize);
            const newTypes = new Array(newSize);
            const newTypeIndices = new Uint8Array(newSize);

            // Copy existing data
            newPositions.set(this.positions);
            newVelocities.set(this.velocities);
            newColors.set(this.colors);
            newEnergies.set(this.energies);

            for (let i = 0; i < currentSize; i++) {
                newTypes[i] = this.types[i];
                newTypeIndices[i] = this.typeIndices[i];
            }

            // Replace arrays
            this.positions = newPositions;
            this.velocities = newVelocities;
            this.colors = newColors;
            this.energies = newEnergies;
            this.types = newTypes;
            this.typeIndices = newTypeIndices;

            // Update rendering
            this.pointCloudSystem.geometry.setAttribute(
                'position',
                new THREE.BufferAttribute(this.positions, 3)
            );
            this.pointCloudSystem.geometry.setAttribute(
                'color',
                new THREE.BufferAttribute(this.colors, 3)
            );

            const sizes = new Float32Array(newSize);
            for (let i = 0; i < newSize; i++) {
                sizes[i] = 0.2 + this.energies[i] * 0.2;
            }
            this.pointCloudSystem.geometry.setAttribute(
                'size',
                new THREE.BufferAttribute(sizes, 1)
            );
        }
    }

    getParticleTypeFromPosition(gridPosition) {
        if (this.controller?.topical) {
            return this.controller.topical.getTypeFromPosition(gridPosition);
        }
        return 'a';
    }

    setController(controller) {
        this.controller = controller;
        this.scene.userData.controller = controller;
    }

    updateFromController() {
        if (this.controller?.params) {
            // Update particle data from controller
            const typeMatrix = this.controller.params.typeMatrix;
            const particleTypes = this.controller.params.particleTypes;
            const globalAttraction = this.controller.params.globalAttraction;
            const globalRepulsion = this.controller.params.globalRepulsion;

            // Store in scene userData for access during physics update
            this.scene.userData.particles = {
                typeMatrix, particleTypes, globalAttraction, globalRepulsion
            };
        }
    }

    transformParticles() {
        const particleCount = this.positions.length / 3;
        const transformThreshold = 3.0; // Distance threshold for transformation
        const transformChance = 0.01; // Probability of transformation per eligible particle

        // Only process a subset of particles each frame
        const chunkSize = Math.ceil(particleCount / this.updateEveryNthParticle);
        const startIdx = (this.frameCount % this.updateEveryNthParticle) * chunkSize;
        const endIdx = Math.min(startIdx + chunkSize, particleCount);

        for (let i = startIdx; i < endIdx; i++) {
            // Skip with probability
            if (Math.random() > transformChance) continue;

            const idx = i * 3;
            const type = this.types[i];
            const neighbors = this.getNeighborIndices(i);

            // Count particles by type within threshold
            const typeCounts = {};
            let totalNearby = 0;

            for (const j of neighbors) {
                if (i === j) continue;

                const otherIdx = j * 3;

                // Calculate distance squared
                const dx = this.positions[otherIdx] - this.positions[idx];
                const dy = this.positions[otherIdx + 1] - this.positions[idx + 1];
                const dz = this.positions[otherIdx + 2] - this.positions[idx + 2];
                const distSq = dx*dx + dy*dy + dz*dz;

                // If within transformation threshold
                if (distSq < transformThreshold) {
                    const otherType = this.types[j];
                    typeCounts[otherType] = (typeCounts[otherType] || 0) + 1;
                    totalNearby++;
                }
            }

            // Only transform if enough nearby particles
            if (totalNearby >= 5) {
                // Find dominant type
                let dominantType = type;
                let maxCount = 0;

                for (const [neighborType, count] of Object.entries(typeCounts)) {
                    if (count > maxCount && neighborType !== type) {
                        maxCount = count;
                        dominantType = neighborType;
                    }
                }

                // If dominant type is different from current type
                if (dominantType !== type && maxCount >= 3) {
                    // Transform this particle
                    this.transformParticle(i, dominantType);

                    // Apply opposite reaction - transform a random particle of dominant type to this type
                    const eligibleForReverse = neighbors.filter(j =>
                        this.types[j] === dominantType &&
                        Math.random() < 0.3 // Only 30% chance of reverse transformation
                    );

                    if (eligibleForReverse.length > 0) {
                        const reverseIdx = eligibleForReverse[Math.floor(Math.random() * eligibleForReverse.length)];
                        this.transformParticle(reverseIdx, type);
                    }
                }
            }
        }
    }

    transformParticle(index, newType) {
        // Store previous type for any needed reference
        const oldType = this.types[index];

        // Update type
        this.types[index] = newType;
        this.typeIndices[index] = newType.charCodeAt(0) - 97;

        // Update color
        const idx = index * 3;
        if (this.controller?.params.particleTypes) {
            const typeData = this.controller.params.particleTypes[newType];
            const color = new THREE.Color(typeData.color);
            this.colors[idx] = color.r;
            this.colors[idx + 1] = color.g;
            this.colors[idx + 2] = color.b;
        } else {
            const typeIndex = newType.charCodeAt(0) - 97;
            this.colors[idx] = (typeIndex % 3 === 0) ? 1 : 0.3;
            this.colors[idx + 1] = (typeIndex % 3 === 1) ? 1 : 0.3;
            this.colors[idx + 2] = (typeIndex % 3 === 2) ? 1 : 0.3;
        }

        // Apply energy boost to transformed particle
        this.energies[index] = Math.min(this.energies[index] + 0.5, 2.0);

        // Mark colors as needing update
        if (this.pointCloudSystem?.geometry?.attributes.color) {
            this.pointCloudSystem.geometry.attributes.color.needsUpdate = true;
        }
    }
}
