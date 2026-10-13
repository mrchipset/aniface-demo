from PIL import Image
im = Image.open(r"racc_tex_Image_0_001.png").convert("RGB")
W,H = im.size
# texture v=0 is the BOTTOM of the image -> head island (high v) is near the TOP of the PNG
crop = im.crop((0, 0, 280, 190)).resize((280*3, 190*3), Image.NEAREST)
crop.save(r"head_island_zoom.png")
print("saved head_island_zoom.png", crop.size)
