from argparse import ArgumentParser
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "chars"
DEFAULT_SOURCE = Path.home() / "Downloads" / "Pixel Portrait" / "Pixel-Portraits-Free"

BODIES = {
    "ma": ("Masculine_A", "masculine_A"),
    "mb": ("Masculine_B", "masculine_B"),
    "fa": ("Feminine_A", "feminine_A"),
    "fb": ("Feminine_B", "feminine_B"),
}

HAIR_TILES = {
    ("ma", "A"): (0, 2),
    ("ma", "B"): (1, 2),
    ("ma", "C"): (2, 2),
    ("mb", "A"): (3, 2),
    ("mb", "B"): (0, 3),
    ("fa", "A"): (0, 0),
    ("fb", "A"): (1, 0),
}

PORTRAITS = {
    "don_ramon": {"body": "ma", "face": "default", "hair": ("brown", "C"), "beard": "F", "glasses": "B"},
    "lola_rosing": {"body": "fa", "face": "happy", "hair": ("colorless", "A")},
    "ms_reyes": {"body": "fb", "face": "happy", "hair": ("brown", "A"), "glasses": "A"},
    "engr_santos": {"body": "ma", "face": "default", "hair": ("brown", "B"), "beard": "A", "glasses": "B"},
    "kuya_boy": {"body": "ma", "face": "annoyed", "hair": ("brown", "A"), "beard": "D"},
    "boss_erning": {"body": "ma", "face": "happy", "hair": ("brown", "C"), "beard": "B"},
    "kap_luz": {"body": "fb", "face": "annoyed", "hair": ("brown", "A")},
    "atty_villaflor": {"body": "fa", "face": "default", "hair": ("colorless", "A"), "glasses": "C"},
    "sir_jepoy": {"body": "mb", "face": "happy", "hair": ("blue", "B"), "glasses": "C"},
    "nanay_merly": {"body": "fa", "face": "sad", "hair": ("brown", "A")},
    "vm_ging": {"body": "fb", "face": "happy", "hair": ("brown", "A")},
    "carlo": {"body": "mb", "face": "happy", "hair": ("yellow", "A"), "glasses": "A"},
    "typhoon": {"body": "fb", "face": "sad", "hair": ("brown", "A")},
    "fiesta": {"body": "ma", "face": "happy", "hair": ("brown", "A"), "beard": "E"},
    "scandal": {"body": "fa", "face": "annoyed", "hair": ("brown", "A"), "glasses": "B"},
    "ribbon": {"body": "mb", "face": "happy", "hair": ("brown", "B")},
    "debate": {"body": "fb", "face": "default", "hair": ("brown", "A")},
    "brownout": {"body": "ma", "face": "angry", "hair": ("brown", "B"), "beard": "C"},
    "dengue": {"body": "ma", "face": "default", "hair": ("brown", "C"), "beard": "F", "glasses": "A"},
    "jeepney": {"body": "ma", "face": "annoyed", "hair": ("brown", "A"), "beard": "F"},
    "graduation": {"body": "fa", "face": "default", "hair": ("colorless", "A")},
    "callin": {"body": "mb", "face": "happy", "hair": ("pink", "A"), "glasses": "C"},
    "mayor_male": {"body": "ma", "face": "default", "hair": ("brown", "C"), "beard": "F"},
    "mayor_female": {"body": "fa", "face": "happy", "hair": ("brown", "A")},
}


def base_path(source: Path, body: str, face: str) -> Path:
    folder, stem = BODIES[body]
    for separator in ("_", "-"):
        path = source / folder / f"{stem}{separator}{face}.png"
        if path.is_file():
            return path
    raise FileNotFoundError(path)


def hair_layer(source: Path, color: str, style: str, body: str) -> Image.Image:
    col, row = HAIR_TILES[(body, style)]
    sheet = Image.open(source / "Hair" / f"{color}_hair-sheet.png").convert("RGBA")
    return sheet.crop((col * 64, row * 96, (col + 1) * 64, (row + 1) * 96))


def compose(source: Path, spec: dict) -> Image.Image:
    canvas = Image.open(base_path(source, spec["body"], spec["face"])).convert("RGBA")
    color, style = spec["hair"]
    canvas.alpha_composite(hair_layer(source, color, style, spec["body"]))
    if beard := spec.get("beard"):
        name = f"Beard_{beard}_masculine_A-base.png"
        canvas.alpha_composite(Image.open(source / "Masculine_A" / name).convert("RGBA"))
    if glasses := spec.get("glasses"):
        name = f"Glasses_{glasses}.png"
        canvas.alpha_composite(Image.open(source / "Accessories" / name).convert("RGBA"))
    return canvas


def trim(canvas: Image.Image) -> Image.Image:
    box = canvas.getbbox()
    if not box:
        return canvas
    left, top, right, bottom = box
    return canvas.crop((max(0, left - 1), max(0, top - 1), min(canvas.width, right + 1), min(canvas.height, bottom + 1)))


def main():
    parser = ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for cid, spec in PORTRAITS.items():
        canvas = compose(args.source, spec)
        full = trim(canvas)
        full.resize((256, round(full.height * 256 / full.width)), Image.Resampling.NEAREST).save(
            OUT / f"{cid}.png", optimize=True
        )
        canvas.crop((8, 28, 56, 76)).resize((192, 192), Image.Resampling.NEAREST).save(
            OUT / f"avatar_{cid}.png", optimize=True
        )
    print(f"Wrote {len(PORTRAITS) * 2} portraits to {OUT}")


if __name__ == "__main__":
    main()
