from PIL import Image
import os


def delete_background(image, directory):
    img = Image.open('{}\\{}'.format(directory, image)).convert('RGBA')
    if img.mode == "RGB":
        a_channel = Image.new('L', img.size, 255)  # 'L' 8-bit pixels, black and white
        img.putalpha(a_channel)
    pixels = img.load()
    for wPixel in range(img.size[0]):
        for hPixel in range(img.size[1]):
            r, g, b, a = pixels[wPixel, hPixel]
            if (r,g,b) == (255, 255, 255):
                pixels[wPixel, hPixel] = 255, 255, 255, 0
    return img


if __name__ == '__main__':
    directory = 'icons'
    for skin in os.listdir(directory):
        delete_background(skin, directory).save('{}\\{}'.format(directory, skin))
