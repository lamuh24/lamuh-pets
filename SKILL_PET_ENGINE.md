# Lamuh Pet Engine Framework (Web-to-PiP)

## Overview
A lightweight, high-performance digital companion engine that leverages the modern Web PiP (Picture-in-Picture) API to create "always-on-top" desktop pets. This framework allows for instant character creation and deployment via a browser-based studio.

## Key Capabilities
- **Document PiP Orchestration**: Spawns a dedicated, minimal window for the pet that persists over other applications.
- **Optimized Sprite Animation**: Efficient 12x8 grid stepping logic for smooth character movement and states.
- **Universal Character Importer**: Handles local files and data URLs for rapid character swapping.
- **PiP-to-Host Sync**: Synchronizes animation states and speeds between the main studio and the popped-out window.
- **AI Prompt Engineering**: Integrated logic to generate perfectly aligned 12x8 spritesheets using generative AI models.

## Implementation Patterns

### 1. PiP Window Lifecycle (`requestWindow`)
- Requests a window with specific dimensions (e.g., 192x208).
- Injecting styles for `-webkit-app-region: drag` to allow the user to move the pet by clicking anywhere on it.
- Moving the DOM node directly from the host document to the PiP document to preserve state.

### 2. Animation Logic (CSS Steps)
- Uses `background-position-x` with `steps(8)` for horizontal animation.
- Uses `background-position-y` to switch between 12 distinct behavioral rows (Idle, Run, Jump, etc.).

### 3. AI Spritesheet Prompting
- The core "Magic Prompt" ensures a perfectly aligned 12x8 grid, transparent background, and consistent character pose.
- **Prompt Blueprint**: "A 2D pixel art sprite sheet contact sheet on a solid transparent background... perfectly aligned 12x8 grid of animation frames... 8 frames horizontally, 12 rows vertically."

## Customization Guide (The "Desktop Pet" Workflow)
1. **Character Design**: Use the Prompt Generator to create a new `.webp` or `.png` spritesheet.
2. **Behavioral Config**: Update the `animation-state` select options to match the rows of the new spritesheet.
3. **Dimensions**: Adjust `--frame-width` and `--frame-height` in `:root` if using a different grid size.
4. **PiP Setup**: Ensure `documentPictureInPicture.requestWindow` uses the matching frame dimensions.

## Files to Reference
- [index.html](file:///c:/Users/qchee/.codex/avatars/lamuh/lamuh%20pets/index.html): The complete engine logic, including PiP and animation.
- [spritesheet.webp](file:///c:/Users/qchee/.codex/avatars/lamuh/lamuh%20pets/spritesheet.webp): The reference 12x8 animation asset.
