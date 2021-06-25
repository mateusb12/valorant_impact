import os
import numpy as np
import matplotlib.pyplot as plt
import imageio

# y = np.random.randint(30, 40, size=40)
#
# plt.plot(y)
# plt.ylim(20, 50)
# plt.show()
#
# # ONE
# plt.plot(y[:-3])
# plt.ylim(20, 50)
# plt.savefig('1.png')
# plt.show()
#
# # TWO
# plt.plot(y[:-2])
# plt.ylim(20, 50)
# plt.savefig('2.png')
# plt.show()
#
# # THREE
# plt.plot(y[:-1])
# plt.ylim(20, 50)
# plt.savefig('3.png')
# plt.show()
#
# # FOUR
# plt.plot(y)
# plt.ylim(20, 50)
# plt.savefig('4.png')
# plt.show()

# with imageio.get_writer('my_gif.gif', mode='I') as writer:
#     for filename in ['1.png', '2.png', '3.png', '4.png']:
#         image = imageio.imread(filename)
#         writer.append_data(image)

y = np.random.randint(30, 40, size=40)
filenames = []
for i in y:
    plt.plot(y[:i])
    plt.ylim(20, 50)

    filename = f'{i}.png'
    filenames.append(filename)

    plt.savefig(filename)
    plt.close()
