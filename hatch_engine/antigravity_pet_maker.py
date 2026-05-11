import argparse
import os
import json
from PIL import Image, ImageChops

CELL_W = 192
CELL_H = 208
COLS = 8
ROWS = 9
ATLAS_W = CELL_W * COLS
ATLAS_H = CELL_H * ROWS

def get_frames_dir():
    d = "frames"
    os.makedirs(d, exist_ok=True)
    return d

def remove_chroma_key(img, key_color=(255, 0, 255), tolerance=30):
    img = img.convert("RGBA")
    data = img.getdata()
    new_data = []
    
    kr, kg, kb = key_color
    
    for item in data:
        r, g, b, a = item
        # Calculate naive color distance
        dist = abs(r - kr) + abs(g - kg) + abs(b - kb)
        if dist < tolerance:
            new_data.append((255, 255, 255, 0)) # transparent
        else:
            new_data.append(item)
            
    img.putdata(new_data)
    return img

def cmd_init(args):
    print(f"Initializing pet: {args.name}")
    req = {
        "id": args.name.lower().replace(" ", "_"),
        "displayName": args.name,
        "description": args.desc
    }
    with open("pet_request.json", "w") as f:
        json.dump(req, f, indent=2)
    os.makedirs("frames", exist_ok=True)
    os.makedirs("final", exist_ok=True)
    print("Run environment created. You can now generate images and run 'process_row'.")

def cmd_process_row(args):
    print(f"Processing row {args.row} from {args.input_image}")
    try:
        img = Image.open(args.input_image).convert("RGBA")
    except Exception as e:
        print(f"Error opening image: {e}")
        return
        
    # Assume the generated strip has frames horizontally
    img_w, img_h = img.size
    # Resize or assume it fits
    
    # Remove background
    key_color = tuple(map(int, args.chroma.split(',')))
    img_transparent = remove_chroma_key(img, key_color)
    
    # Extract frames
    frames_dir = get_frames_dir()
    for col in range(COLS):
        # We assume the strip is either COLS*CELL_W wide, or we just extract evenly
        box_w = img_w // COLS
        box = (col * box_w, 0, (col + 1) * box_w, img_h)
        frame = img_transparent.crop(box)
        
        # Resize to exact cell
        frame = frame.resize((CELL_W, CELL_H), Image.Resampling.LANCZOS)
        
        out_path = os.path.join(frames_dir, f"r{args.row}_c{col}.png")
        frame.save(out_path)
    print(f"Row {args.row} extracted to {frames_dir}/")

def cmd_mirror_row(args):
    print(f"Mirroring row {args.src_row} to {args.dest_row}")
    frames_dir = get_frames_dir()
    for col in range(COLS):
        src_path = os.path.join(frames_dir, f"r{args.src_row}_c{col}.png")
        if os.path.exists(src_path):
            img = Image.open(src_path)
            mirrored = img.transpose(Image.FLIP_LEFT_RIGHT)
            dest_path = os.path.join(frames_dir, f"r{args.dest_row}_c{col}.png")
            mirrored.save(dest_path)
    print("Mirroring complete.")

def cmd_package(args):
    print("Packaging atlas...")
    frames_dir = get_frames_dir()
    atlas = Image.new("RGBA", (ATLAS_W, ATLAS_H), (0,0,0,0))
    
    for r in range(ROWS):
        for c in range(COLS):
            path = os.path.join(frames_dir, f"r{r}_c{c}.png")
            if os.path.exists(path):
                frame = Image.open(path).convert("RGBA")
                atlas.paste(frame, (c * CELL_W, r * CELL_H))
                
    out_dir = "final"
    os.makedirs(out_dir, exist_ok=True)
    atlas.save(os.path.join(out_dir, "spritesheet.webp"), "WEBP")
    atlas.save(os.path.join(out_dir, "spritesheet.png"), "PNG")
    
    # Read req
    if os.path.exists("pet_request.json"):
        with open("pet_request.json", "r") as f:
            req = json.load(f)
    else:
        req = {"id": "custom", "displayName": "Custom Pet", "description": ""}
        
    req["spritesheetPath"] = "spritesheet.webp"
    
    with open(os.path.join(out_dir, "pet.json"), "w") as f:
        json.dump(req, f, indent=2)
        
    print(f"Validation: Atlas size is {atlas.size} (Expected: {ATLAS_W}x{ATLAS_H})")
    print(f"Packaged successfully to {out_dir}/")

def cmd_qa(args):
    print("Generating QA HTML Previewer...")
    out_dir = "final"
    os.makedirs(out_dir, exist_ok=True)
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Pet QA Preview</title>
    <style>
        body { background: #1a1a1a; color: white; font-family: sans-serif; display: flex; flex-direction: column; align-items: center; padding: 50px; }
        .pet-container { width: 192px; height: 208px; background: rgba(255,255,255,0.05); border: 1px solid #333; position: relative; overflow: hidden;}
        .pet-sprite { width: 100%; height: 100%; background-image: url('spritesheet.webp'); background-repeat: no-repeat; background-position: 0px 0px; animation: playSprite 0.8s steps(8) infinite; }
        @keyframes playSprite { from { background-position-x: 0px; } to { background-position-x: -1536px; } }
        select { margin-top: 20px; padding: 10px; background: #333; color: white; border: none; outline: none; }
    </style>
</head>
<body>
    <h2>Pet QA Preview</h2>
    <div class="pet-container"><div class="pet-sprite" id="pet"></div></div>
    <select id="state">
        <option value="0">Row 0 - Idle</option>
        <option value="1">Row 1 - Running Right</option>
        <option value="2">Row 2 - Running Left</option>
        <option value="3">Row 3 - Waving</option>
        <option value="4">Row 4 - Jumping</option>
        <option value="5">Row 5 - Failed</option>
        <option value="6">Row 6 - Waiting</option>
        <option value="7">Row 7 - Running</option>
        <option value="8">Row 8 - Review</option>
    </select>
    <script>
        const sel = document.getElementById('state');
        sel.addEventListener('change', (e) => {
            document.getElementById('pet').style.backgroundPositionY = `-${parseInt(e.target.value) * 208}px`;
        });
        sel.dispatchEvent(new Event('change'));
    </script>
</body>
</html>"""
    with open(os.path.join(out_dir, "index.html"), "w") as f:
        f.write(html_content)
        
    bat_content = '@echo off\nstart "" "index.html"\nexit'
    with open(os.path.join(out_dir, "run_pet.bat"), "w") as f:
        f.write(bat_content)
        
    print(f"QA tools generated in {out_dir}/! Open index.html to preview.")

def main():
    parser = argparse.ArgumentParser(description="Antigravity Hatch Pet Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Init
    p_init = subparsers.add_parser("init")
    p_init.add_argument("--name", required=True)
    p_init.add_argument("--desc", default="A custom generated pet.")
    
    # Process Row
    p_row = subparsers.add_parser("process_row")
    p_row.add_argument("--input_image", required=True)
    p_row.add_argument("--row", type=int, required=True)
    p_row.add_argument("--chroma", default="255,0,255", help="RGB comma separated")
    
    # Mirror Row
    p_mirror = subparsers.add_parser("mirror_row")
    p_mirror.add_argument("--src_row", type=int, required=True)
    p_mirror.add_argument("--dest_row", type=int, required=True)
    
    # Package
    p_pkg = subparsers.add_parser("package")
    
    # QA
    p_qa = subparsers.add_parser("qa")
    
    args = parser.parse_args()
    
    if args.command == "init": cmd_init(args)
    elif args.command == "process_row": cmd_process_row(args)
    elif args.command == "mirror_row": cmd_mirror_row(args)
    elif args.command == "package": cmd_package(args)
    elif args.command == "qa": cmd_qa(args)

if __name__ == "__main__":
    main()
