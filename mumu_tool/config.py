devices1 = {
    "clone-1": 16448,
    "clone-2": 16480,
    "clone-3": 16512,
    "clone-4": 16544,
    "clone-5": 16576,
    "clone-6": 16608,
    "clone-7": 16640,
    "clone-8": 16672,
    "clone-9": 16704,
    "clone-10": 16736,
    "clone-11": 16768,
    "clone-12": 16800,
    "clone-13": 16832,
    "clone-14": 16864,
    "clone-15": 16896,
    "clone-16": 16928,
    "clone-17": 16960,
    "clone-18": 16992,
    "clone-19": 17024,
    "clone-20": 17056,
}

devices2 = {
    # "clone-21": 16928,
    # "clone-22": 17120,
    # "clone-23": 17152,
    # "clone-24": 17184,
}

# mặc định dùng group 1
devices = devices1
merge_devices = {**devices1, **devices2}
