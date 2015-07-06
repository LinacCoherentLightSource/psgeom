# psgeom
preliminary code for represting geometry of scattering experiments

**Warning** : code in this repo is preliminary. It may contain bugs. The right to change interfaces, names, or functionality is reserved until further notice. The official LCLS geometry representation code can be found in the PSCalib module.

Here's a quick example of how to use this code. Imagine I have a geometry file
on the psana machines `1-end.data` that I want to load and manipulate. You can
find an example of such a file in the `ref_files` directory in this repo.

Then,

```
from psgeom import detector

dtc = detector.CSPAD.from_psana_file('1-end.data')
print dtc.draw_tree()
print dtc.xyz

dtc.to_cheetah_file('my_new_cheetah_geom.h5')
```

Functionality left to add:
* documentation, some is there, but more is good.
* smart ways to visualize the geometry and intensities
* additional sensor elements
* If requested, legacy interface to mimic PSCalib


