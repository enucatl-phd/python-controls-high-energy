import h5py

class Hdf5Writer(object):

    def __init__(self, filename, num_image_per_file=None, nexus=None, compression=None):
        # unused args to get the same interface as dectris.albula.Hdf5Writer
        super(Hdf5Writer, self).__init__()
        self.filename = filename
        self.image_id = 1

    def open(self):
        self.file = h5py.File(self.filename)

    def close(self):
        self.file.close()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def write(self, dimage):
        group = self.file.require_group("/entry/data")
        dataset = group.create_dataset(
            "data_{0:06d}".format(self.image_id),
            data=dimage.data()
        )
        self.image_id += 1
