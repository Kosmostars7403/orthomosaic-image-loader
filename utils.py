def is_image(filename: str) -> bool:
    extensions = {
        'jpg': True,
        'png': True,
        'jpeg': True,
        'JPG': True,
        'PNG': True,
        'JPEG': True
    }

    return filename.split('.')[-1] in extensions
