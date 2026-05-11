Lamuh Shonen Interaction Import Pack

Files:
- lamuh_interactions_spritesheet_3x8.png / .webp: combined 3-row sheet, 1536x624.
- lamuh_interaction_naruto_hand_signs.png / .webp: 8-frame strip, 1536x208.
- lamuh_interaction_conqueror_gear_pose.png / .webp: 8-frame strip, 1536x208.
- lamuh_interaction_dragon_ball_beam_clash.png / .webp: 8-frame strip, 1536x208.
- lamuh_interactions_manifest.json: import metadata.
- preview.html: quick browser preview.
- source_generations/: untouched copies of the original generated images.

Import contract:
- Frame size: 192x208
- Frames per animation: 8
- Background: transparent alpha
- Source chroma key removed: #FF00FF
- Individual strip size: 1536x208
- Combined sheet size: 1536x624

Suggested state names:
- naruto_hand_signs
- conqueror_gear_pose
- dragon_ball_beam_clash

Extended drop-in option:
- lamuh_extended_spritesheet_12x8.png / .webp: original Lamuh 9-row sheet plus 3 new interaction rows, 1536x2496.
- pet_shonen_extended.json: metadata for the 12-row sheet.
- pet_py_state_map_patch.json: row indexes to add if your engine needs explicit state map entries.

Extended rows:
- row 9: naruto_hand_signs
- row 10: conqueror_gear_pose
- row 11: dragon_ball_beam_clash
