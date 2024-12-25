import rawpy
import matplotlib.pyplot as plt
from os import listdir
import numpy as np
from win32com.shell import shell, shellcon
from os import startfile
from consolemenu import SelectionMenu
import PIL
from PIL.ExifTags import TAGS, IFD, GPSTAGS
import pandas as pd
import cv2
from math import isnan


def crop_image_array(arr, x1, x2, y1, y2):
    return arr[y1:y2, x1:x2]


def delete_image(path):
    res = shell.SHFileOperation((0, shellcon.FO_DELETE, path, None,
        shellcon.FOF_SILENT | shellcon.FOF_ALLOWUNDO | shellcon.FOF_NOCONFIRMATION,
        None, None))


def get_image(path, bounds=None):
    with rawpy.imread(path) as raw:
        rgb = raw.postprocess()
        arr = np.array(rgb)

        if bounds is not None:
            arr = crop_image_array(arr, *bounds)

    return arr


def get_image_metadata(path):
    with PIL.Image.open(path) as raw:
        exif = raw.getexif()
        result = {}

        for ifd_id in IFD:
            try:
                ifd = exif.get_ifd(ifd_id)
                resolve = TAGS

                for k, v in ifd.items():
                    tag = resolve.get(k, k)
                    result[tag] = v
            except KeyError:
                pass

    datarow = [
        path.split('/')[-1],
        result['ExposureTime'],
        result['ISOSpeedRatings']
    ]

    return datarow


def get_first_last_composite_image(paths):
    arr = np.array(get_image(paths[0])) + np.array(get_image(paths[-1]))
    arr = np.array(np.round(arr / 2), dtype=np.uint8)
    return arr


def get_paths(folder):
    return [f'{folder}/{file}' for file in listdir(folder) if file.lower().endswith('.nef')]


def show_image(image):   
    plt.imshow(image)
    plt.show()
            
            
def read_metadata(image_paths):
    metadata = []

    for i, path in enumerate(image_paths):
        print(f'Loading image {i+1} of {len(image_paths)}...', end='\r')
        metadata.append(get_image_metadata(path))

    df = pd.DataFrame(metadata, columns=['Filename','Exposure','ISO'])
    df.to_excel('metadata.xlsx')
    startfile('metadata.xlsx')


def roundness_check(image_paths):
    roundness_by_image = {}

    for path in image_paths:
        roundness = []
        print('Checking', path.split('/')[-1], end='')
        img = get_image(path)

        # use the middle 1/3 of the image to evaluate roundness to neglect lens aberrations
        crop_y, crop_x, _ = [int(x / 3) for x in img.shape]
        img = crop_image_array(img, crop_x, 2 * crop_x, crop_y, 2 * crop_y)

        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        _, img_bin = cv2.threshold(img_gray, 240, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(img_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            if len(contour) < 5:
                continue
            
            ellipse = cv2.fitEllipse(contour)  # a is major axis, b is minor axis
            (x,y), (a,b), angle = ellipse

            if a * b == 0 or isnan(a) or isnan(b) or a > 50 or b > 50:
                continue  # if either value is zero, NaN, or too large

            roundness.append(a / b)
        
        avg_roundness = sum(roundness) / len(roundness)
        roundness_by_image[path] = avg_roundness
        print(f' -> {avg_roundness:.3f}')

    plt.ion()
    step = 0.05
    thresholds = np.arange(0, 1, step)
    counts = [np.sum(list(roundness_by_image.values()) < threshold) for threshold in thresholds]
    plt.plot(thresholds, counts, marker='o')
    plt.xticks(thresholds, rotation=45)
    plt.grid()
    plt.xlabel('Roundness threshold')
    plt.ylabel('Rejected images')
    plt.show()
    threshold = float(input('Select threshold to use: '))

    for kv in roundness_by_image.items():
        print(kv)

    paths_to_delete = [item[0] for item in roundness_by_image.items() if item[1] < threshold]
    
    for path in paths_to_delete:
        print(f'Deleting {path}...')
        delete_image(path)


def main():
    options = ['Filter images by star roundness', 'Export metadata']
    selection = SelectionMenu(options)
    selection.show()

    if selection.current_option == len(options):  # exit option
        return
    
    folder = input('Enter folder path: ')
    image_paths = get_paths(folder)

    if selection.current_option == 0:  # star roundness option
        roundness_check(image_paths)
    elif selection.current_option == 1:  # metadata option
        read_metadata(image_paths)

if __name__ == "__main__":
    while True:
        main()