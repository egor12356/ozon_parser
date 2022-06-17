import os



size = os.stat('img/9785448408618_1.jpg').st_size

print(size / 1000)

