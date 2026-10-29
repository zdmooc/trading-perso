"""Dessine les icônes de l'app (bougies vertes et rouges). Usage : python scripts/icones.py"""
from pathlib import Path

from PIL import Image, ImageDraw

FOND, VERT, ROUGE, BLANC = (13, 17, 23, 255), (34, 160, 107, 255), (229, 72, 77, 255), (255, 255, 255, 255)
# (x, mèche haut, corps haut, corps bas, mèche bas, couleur) sur une grille de 100
BOUGIES = [(26, 52, 58, 76, 82, ROUGE), (42, 40, 46, 64, 70, VERT), (58, 30, 36, 54, 62, VERT), (74, 16, 22, 42, 50, VERT)]


def dessiner(taille: int, fond, echelle: float = 1.0, mono: bool = False) -> Image.Image:
    im = Image.new("RGBA", (taille, taille), fond)
    d = ImageDraw.Draw(im)
    k = taille / 100 * echelle
    o = taille * (1 - echelle) / 2
    for x, mh, ch, cb, mb, c in BOUGIES:
        c = BLANC if mono else c
        d.rectangle([o + (x - 0.8) * k, o + mh * k, o + (x + 0.8) * k, o + mb * k], fill=c)
        d.rounded_rectangle([o + (x - 5) * k, o + ch * k, o + (x + 5) * k, o + cb * k], radius=1.5 * k, fill=c)
    return im


ici = Path(__file__).resolve().parent.parent / "assets"
dessiner(1024, FOND, 0.8).convert("RGB").save(ici / "icon.png")
dessiner(1024, (0, 0, 0, 0), 0.5).save(ici / "splash-icon.png")
dessiner(512, (0, 0, 0, 0), 0.6).save(ici / "android-icon-foreground.png")
Image.new("RGBA", (512, 512), FOND).save(ici / "android-icon-background.png")
dessiner(432, (0, 0, 0, 0), 0.6, mono=True).save(ici / "android-icon-monochrome.png")
dessiner(48, FOND, 0.9).save(ici / "favicon.png")
