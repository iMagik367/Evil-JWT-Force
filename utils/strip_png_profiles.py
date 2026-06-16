from PIL import Image
import os


def strip_icc_profiles():
    assets_dir = os.path.join(os.path.dirname(__file__), '..', 'gui', 'assets')
    assets_dir = os.path.abspath(assets_dir)
    if not os.path.isdir(assets_dir):
        print(f"Assets directory not found: {assets_dir}")
        return
    for fname in os.listdir(assets_dir):
        if fname.lower().endswith('.png'):
            path = os.path.join(assets_dir, fname)
            try:
                img = Image.open(path)
                data = list(img.getdata())
                new_img = Image.new(img.mode, img.size)
                new_img.putdata(data)
                new_img.save(path)
                print(f'Stripped profile: {fname}')
            except Exception as e:
                print(f'Error processing {fname}: {e}')


if __name__ == '__main__':
    strip_icc_profiles() 