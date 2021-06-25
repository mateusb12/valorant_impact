import os
import numpy as np
import matplotlib.pyplot as plt
import imageio

y = np.random.randint(30, 40, size=40)

filenames = []

for i in range(40, 0, -1):
    plt.plot(y[:-i])
    plt.ylim(20, 50)
    filename = f'{len(y[:-i])}.png'
    filenames.append(filename)
    plt.savefig('pics/{}'.format(filename))
    plt.close()

with imageio.get_writer('my_gif.gif') as writer:
    for filename in filenames:
        image = imageio.imread('pics/{}'.format(filename))
        writer.append_data(image)

    for filename in set(filenames):
        os.remove('pics/{}'.format(filename))