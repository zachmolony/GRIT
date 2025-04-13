/**
 * @title Animated Eyes - Synchronized Movement with Multiple Effect Modes
 * @desc Draw two ASCII eyes that move together with various background effects.
 */

// Density string not used here; we use explicit symbols for eyes.
const openEyeChar = "*";

// Effect mode toggles
const ENABLE_DOOM_FLAME = false; // Toggle doom flame effect
const ENABLE_PLASMA = true; // Toggle plasma psychedelic effect
const SHOW_EYES_WITH_PLASMA = true; // Whether to show eyes on top of plasma

export const settings = { fps: 50 };

// Helper functions
function fract(x) {
  return x - Math.floor(x);
}
function pseudoRandom(seed) {
  return fract(Math.sin(seed) * 43758.5453123);
}
function lerp(a, b, t) {
  return a + (b - a) * t;
}

// ========== DOOM FLAME MODULE ==========
// Flame character set from dimmest to brightest
const flame = "...::/\\/\\/\\+=*abcdef01XYZ#";
let flameData = [];
let flameCols, flameRows;

// Helper functions for the flame effect
function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function map(value, inMin, inMax, outMin, outMax) {
  return outMin + ((value - inMin) / (inMax - inMin)) * (outMax - outMin);
}

function mix(a, b, t) {
  return a * (1 - t) + b * t;
}

function smoothstep(edge0, edge1, x) {
  const t = clamp((x - edge0) / (edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

// Random int between a and b, inclusive
function rndi(a, b = 0) {
  if (a > b) [a, b] = [b, a];
  return Math.floor(a + Math.random() * (b - a + 1));
}

// Value noise generator
function createValueNoise() {
  const tableSize = 256;
  const r = new Array(tableSize);
  const permutationTable = new Array(tableSize * 2);

  // Create an array of random values and initialize permutation table
  for (let k = 0; k < tableSize; k++) {
    r[k] = Math.random();
    permutationTable[k] = k;
  }

  // Shuffle values of the permutation table
  for (let k = 0; k < tableSize; k++) {
    const i = Math.floor(Math.random() * tableSize);
    // swap
    [permutationTable[k], permutationTable[i]] = [
      permutationTable[i],
      permutationTable[k],
    ];
    permutationTable[k + tableSize] = permutationTable[k];
  }

  return function (px, py) {
    const xi = Math.floor(px);
    const yi = Math.floor(py);

    const tx = px - xi;
    const ty = py - yi;

    const rx0 = xi % tableSize;
    const rx1 = (rx0 + 1) % tableSize;
    const ry0 = yi % tableSize;
    const ry1 = (ry0 + 1) % tableSize;

    // Random values at the corners of the cell using permutation table
    const c00 = r[permutationTable[permutationTable[rx0] + ry0]];
    const c10 = r[permutationTable[permutationTable[rx1] + ry0]];
    const c01 = r[permutationTable[permutationTable[rx0] + ry1]];
    const c11 = r[permutationTable[permutationTable[rx1] + ry1]];

    // Remapping of tx and ty using the Smoothstep function
    const sx = smoothstep(0, 1, tx);
    const sy = smoothstep(0, 1, ty);

    // Linearly interpolate values along the x axis
    const nx0 = mix(c00, c10, sx);
    const nx1 = mix(c01, c11, sx);

    // Linearly interpolate the nx0/nx1 along they y axis
    return mix(nx0, nx1, sy);
  };
}

const noiseFunc = createValueNoise();

// Update flame data for the next frame
function updateFlame(context, cursor) {
  // Detect resize (and initialize buffer if needed)
  if (flameCols !== context.cols || flameRows !== context.rows) {
    flameCols = context.cols;
    flameRows = context.rows;
    flameData = new Array(flameCols * flameRows).fill(0);
  }

  // Fill the floor with some noise
  const t = context.time * 0.0015;
  const last = flameCols * (flameRows - 1);
  for (let i = 0; i < flameCols; i++) {
    const val = Math.floor(map(noiseFunc(i * 0.05, t), 0, 1, 5, 40));
    flameData[last + i] = Math.min(val, flameData[last + i] + 2);
  }

  // Add flames from cursor if pressed
  if (cursor.pressed) {
    const cx = Math.floor(cursor.x);
    const cy = Math.floor(cursor.y);
    flameData[cx + cy * flameCols] = rndi(5, 50);
  }

  // Propagate towards the ceiling with some randomness
  for (let i = 0; i < flameData.length; i++) {
    const row = Math.floor(i / flameCols);
    const col = i % flameCols;
    const dest = row * flameCols + clamp(col + rndi(-1, 1), 0, flameCols - 1);
    const src = Math.min(flameRows - 1, row + 1) * flameCols + col;
    flameData[dest] = Math.max(0, flameData[src] - rndi(0, 2));
  }
}

// Calculate flame character for a specific position
function getFlameChar(x, y) {
  if (!flameCols || !flameRows) return null;

  const index = y * flameCols + x;
  const u = flameData[index];

  if (u === 0) return null; // No flame at this position

  return {
    char: flame[clamp(u, 0, flame.length - 1)],
    fontWeight: u > 20 ? 700 : 100,
    backgroundColor: "black",
    color: "white", // Always white for black and white monitor
  };
}

// ========== PLASMA EFFECT MODULE ==========
const plasma_density = "$?01▄abc+-><:. ";
const PI23 = (Math.PI * 2) / 3;
const PI43 = (Math.PI * 4) / 3;

// Vector operations (simplified versions from vec2 module)
function vec2(x, y) {
  return { x, y };
}
function dot(v1, v2) {
  return v1.x * v2.x + v1.y * v2.y;
}
function sub(v1, v2) {
  return { x: v1.x - v2.x, y: v1.y - v2.y };
}
function length(v) {
  return Math.sqrt(v.x * v.x + v.y * v.y);
}

// Calculate plasma value for a pixel
function calculatePlasma(coord, st, time) {
  const t1 = time * 0.0009;
  const t2 = time * 0.0003;

  const center = vec2(Math.sin(-t1), Math.cos(-t1));
  const v1 = Math.sin(dot(coord, vec2(Math.sin(t1), Math.cos(t1))) * 0.08);
  const v2 = Math.cos(length(sub(st, center)) * 4.0);
  const v3 = v1 + v2;

  return v3;
}

// Get plasma character and background color
function getPlasmaOutput(coord, st, time) {
  const v3 = calculatePlasma(coord, st, time);
  const idx = Math.floor(map(v3, -2, 2, 0, 1) * plasma_density.length);

  // For black and white monitor, use different brightness levels instead of colors
  const brightness = Math.floor(map(v3, -2, 2, 0, 255));

  return {
    char: plasma_density[idx],
    color: "white",
    backgroundColor: "black",
    fontWeight: brightness > 180 ? 800 : brightness > 100 ? 400 : 100,
  };
}

/**
 * Returns a random offset vector (for both eyes) given a seed.
 * The offset ranges between -range and +range.
 */
function getRandomOffset(seed, range = 0.1) {
  return {
    x: (pseudoRandom(seed) - 0.5) * 2 * range,
    y: (pseudoRandom(seed + 1) - 0.5) * 2 * range,
  };
}

/**
 * Generate a random hold time between 0.5 and 4 seconds
 * @param {number} cycleIndex The cycle index to use as seed
 * @returns {number} Random hold time in seconds
 */
function getRandomHoldTime(cycleIndex) {
  return 0.5 + pseudoRandom(cycleIndex * 200) * 3.5; // 0.5 to 4 seconds
}

/**
 * Calculate eye shape based on blink progress
 * @param {number} blinkProgress 0 = fully open, 1 = fully closed
 * @returns {object} Eye shape parameters
 */
function getEyeShape(blinkProgress) {
  // Vertical scale goes from 1 (circle) to 0.05 (nearly flat line)
  const verticalScale = 1.0 - blinkProgress * 0.95;
  return {
    horizontalRadius: 0.4, // Decreased from 0.5 to 0.4 (slightly smaller)
    verticalRadius: 0.4 * verticalScale, // Decreased from 0.5 to 0.4
  };
}

// Somewhere at the top or in your global scope
let lastMoveTime = 0;
let targetX = 0;
let targetY = 0;

// Inside your update logic or main function
export function pre(context, cursor, buffer) {
  if (ENABLE_DOOM_FLAME) {
    updateFlame(context, cursor);
  }
}

export function main(coord, context, cursor, buffer) {
  // Time in seconds.
  const t = context.time * 0.001;
  const m = Math.min(context.cols, context.rows);
  const a = context.metrics.aspect;

  // Normalize current coordinate so that the center of the screen is (0,0)
  const st = {
    x: ((2.0 * (coord.x - context.cols / 2)) / m) * a,
    y: (2.0 * (coord.y - context.rows / 2)) / m,
  };

  // For plasma mode, a reference to raw coordinates is also needed
  const raw_coord = vec2(coord.x, coord.y);

  // If we're in plasma mode, handle that separately
  if (ENABLE_PLASMA) {
    const plasmaResult = getPlasmaOutput(raw_coord, st, context.time);

    // If eyes should appear on top of plasma, calculate eye positions
    if (SHOW_EYES_WITH_PLASMA) {
      // ========== MOVEMENT SYSTEM ==========
      // Find the current cycle by iterating through cycles until we find the one containing time t
      let cycleStartTime = 0;
      let cycleIndex = 0;
      let currentHoldTime = getRandomHoldTime(0);

      // Keep advancing cycles until we find the one containing time t
      while (true) {
        const cycleDuration = currentHoldTime + 0.2; // Transition time
        if (cycleStartTime + cycleDuration > t) {
          // We found the cycle containing time t
          break;
        }

        // Move to the next cycle
        cycleStartTime += cycleDuration;
        cycleIndex++;
        currentHoldTime = getRandomHoldTime(cycleIndex);
      }

      // Calculate phase within the current cycle
      const phase = t - cycleStartTime;

      // Generate previous offset and next offset using the cycle index
      const prevOffset = getRandomOffset(cycleIndex * 100, 0.6);
      const nextOffset = getRandomOffset((cycleIndex + 1) * 100, 0.6);

      // Compute the current position offset
      let currentOffset;
      if (phase < 0.2) {
        // During the brief transition phase, tween from previous offset to the next offset.
        const tNorm = phase / 0.2;
        currentOffset = {
          x: lerp(prevOffset.x, nextOffset.x, tNorm),
          y: lerp(prevOffset.y, nextOffset.y, tNorm),
        };
      } else {
        // Once transition is done, hold the new target offset.
        currentOffset = nextOffset;
      }

      // ========== INDEPENDENT BLINKING SYSTEM ==========
      let blinkProgress = 0; // 0 = eye fully open, 1 = eye fully closed

      // Create occasional blinks based on time
      const averageBlinkDuration = 500.0; // Average time between blinks in seconds

      // Generate a series of blink times using a deterministic approach
      for (let i = 0; i < 100; i++) {
        // Generate a unique blink time for each index
        const blinkSeed = Math.floor(t / averageBlinkDuration) * 1000 + i;
        const blinkOffset =
          pseudoRandom(blinkSeed * 123) * averageBlinkDuration;
        const blinkTime =
          Math.floor(t / averageBlinkDuration) * averageBlinkDuration +
          blinkOffset;

        // If this blink should happen now
        const timeSinceBlink = t - blinkTime;
        if (timeSinceBlink >= 0 && timeSinceBlink < 0.15) {
          // 0.15s for a complete blink
          // Calculate blink progress - first half closing, second half opening
          if (timeSinceBlink < 0.075) {
            blinkProgress = timeSinceBlink / 0.075; // 0 to 1 (closing)
          } else {
            blinkProgress = 1 - (timeSinceBlink - 0.075) / 0.075; // 1 to 0 (opening)
          }
          break; // We found an active blink, no need to check further
        }
      }

      // Base positions for left and right eyes.
      const leftBase = { x: -0.5, y: 0.0 };
      const rightBase = { x: 0.5, y: 0.0 };

      // Both eyes move together using the same offset.
      const leftEyeCenter = {
        x: leftBase.x + currentOffset.x,
        y: leftBase.y + currentOffset.y,
      };
      const rightEyeCenter = {
        x: rightBase.x + currentOffset.x,
        y: rightBase.y + currentOffset.y,
      };

      // Get current eye shape based on blink progress
      const eyeShape = getEyeShape(blinkProgress);

      // Define a simple Euclidean distance function.
      function distance(pt1, pt2) {
        const dx = (pt1.x - pt2.x) / eyeShape.horizontalRadius;
        const dy = (pt1.y - pt2.y) / eyeShape.verticalRadius;
        return Math.sqrt(dx * dx + dy * dy) - 1.0; // -1.0 normalizes the ellipse
      }

      // Compute distances from current pixel to the centers of each eye.
      const dLeft = distance(st, leftEyeCenter);
      const dRight = distance(st, rightEyeCenter);
      const d = Math.min(dLeft, dRight);

      // If the pixel is inside an eye, output the open eye character over plasma
      if (d < 0) {
        return {
          char: openEyeChar,
          backgroundColor: "black",
          color: "white",
          fontWeight: 800,
        };
      }
    }

    // Return plasma effect
    return plasmaResult;
  }

  // If we're not in plasma mode, proceed with original eyes and optional flame
  // Base positions for left and right eyes.
  const leftBase = { x: -0.8, y: 0.0 };
  const rightBase = { x: 0.8, y: 0.0 };

  const transitionTime = 0.2; // Transition between positions happens in 0.2 seconds.
  const blinkTime = 0.15; // Time for a full blink (close and reopen)

  // ========== MOVEMENT SYSTEM ==========
  // Find the current cycle by iterating through cycles until we find the one containing time t
  let cycleStartTime = 0;
  let cycleIndex = 0;
  let currentHoldTime = getRandomHoldTime(0);

  // Keep advancing cycles until we find the one containing time t
  while (true) {
    const cycleDuration = currentHoldTime + transitionTime;
    if (cycleStartTime + cycleDuration > t) {
      // We found the cycle containing time t
      break;
    }

    // Move to the next cycle
    cycleStartTime += cycleDuration;
    cycleIndex++;
    currentHoldTime = getRandomHoldTime(cycleIndex);
  }

  // Calculate phase within the current cycle
  const phase = t - cycleStartTime;

  // Generate previous offset and next offset using the cycle index
  const prevOffset = getRandomOffset(cycleIndex * 100, 0.6);
  const nextOffset = getRandomOffset((cycleIndex + 1) * 100, 0.6);

  // Compute the current position offset
  let currentOffset;
  if (phase < transitionTime) {
    // During the brief transition phase, tween from previous offset to the next offset.
    const tNorm = phase / transitionTime;
    currentOffset = {
      x: lerp(prevOffset.x, nextOffset.x, tNorm),
      y: lerp(prevOffset.y, nextOffset.y, tNorm),
    };
  } else {
    // Once transition is done, hold the new target offset.
    currentOffset = nextOffset;
  }

  // ========== INDEPENDENT BLINKING SYSTEM ==========
  let blinkProgress = 0; // 0 = eye fully open, 1 = eye fully closed

  // Create occasional blinks based on time
  const blinkCheckInterval = 1.0; // Check for potential blinks every second
  const averageBlinkDuration = 500.0; // Average time between blinks in seconds

  // Generate a series of blink times using a deterministic approach
  for (let i = 0; i < 100; i++) {
    // Generate a unique blink time for each index
    const blinkSeed = Math.floor(t / averageBlinkDuration) * 1000 + i;
    const blinkOffset = pseudoRandom(blinkSeed * 123) * averageBlinkDuration;
    const blinkTime =
      Math.floor(t / averageBlinkDuration) * averageBlinkDuration + blinkOffset;

    // If this blink should happen now
    const timeSinceBlink = t - blinkTime;
    if (timeSinceBlink >= 0 && timeSinceBlink < 0.15) {
      // 0.15s for a complete blink
      // Calculate blink progress - first half closing, second half opening
      if (timeSinceBlink < 0.075) {
        blinkProgress = timeSinceBlink / 0.075; // 0 to 1 (closing)
      } else {
        blinkProgress = 1 - (timeSinceBlink - 0.075) / 0.075; // 1 to 0 (opening)
      }
      break; // We found an active blink, no need to check further
    }
  }

  // Both eyes move together using the same offset.
  const leftEyeCenter = {
    x: leftBase.x + currentOffset.x,
    y: leftBase.y + currentOffset.y,
  };
  const rightEyeCenter = {
    x: rightBase.x + currentOffset.x,
    y: rightBase.y + currentOffset.y,
  };

  // Get current eye shape based on blink progress
  const eyeShape = getEyeShape(blinkProgress);

  // Define a simple Euclidean distance function.
  function distance(pt1, pt2) {
    const dx = (pt1.x - pt2.x) / eyeShape.horizontalRadius;
    const dy = (pt1.y - pt2.y) / eyeShape.verticalRadius;
    return Math.sqrt(dx * dx + dy * dy) - 1.0; // -1.0 normalizes the ellipse
  }

  // Compute distances from current pixel to the centers of each eye.
  const dLeft = distance(st, leftEyeCenter);
  const dRight = distance(st, rightEyeCenter);
  const d = Math.min(dLeft, dRight);

  // If the pixel is inside an eye, output the open eye character.
  if (d < 0) {
    return {
      char: openEyeChar,
      backgroundColor: "black",
      color: "white",
      fontWeight: 800,
    };
  }

  // Otherwise, check if we should render flame
  if (ENABLE_DOOM_FLAME) {
    const flameResult = getFlameChar(coord.x, coord.y);
    if (flameResult) return flameResult;
  }

  // Fall back to empty space
  return {
    char: " ",
    backgroundColor: "black",
    color: "white",
  };
}

// import { drawInfo } from "/src/modules/drawbox.js";
// export function post(context, cursor, buffer) {
//   drawInfo(context, cursor, buffer);
// }
