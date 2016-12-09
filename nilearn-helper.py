from nilearn import plotting
import nilearn
import matplotlib
from nistats.thresholding import map_threshold
from matplotlib import pyplot as plt
from IPython.display import display_html
plt.rcParams.update({'figure.max_open_warning': 0})
import nibabel as nib
import numpy as np

def plot_stat_map(img, row_l, start, end, step, title, threshold=None, axis='z', method='plot_stat_map', overlay=None):
    slice_nb = int(abs(((end - start) / float(step))))
    for line in range(int(slice_nb/float(row_l) + 1)):
        opt = {'title':{True:title,
                        False:None}[line==0],
               'colorbar':True,
               'black_bg':True,
               'display_mode':axis,
               'threshold':threshold,
               'cmap': plotting.cm.blue_transparent,
               'cut_coords':range(start + line * row_l * step,
                                       start + (line+1) * row_l * step,
                                       step)}
        if method == 'plot_prob_atlas':
            opt.update({'maps_img': img,
                        'view_type': 'contours'})
        elif method == 'plot_stat_map':
            opt.update({'stat_map_img': img})

        t = getattr(plotting, method).__call__(**opt)

        # Add overlay
        if not overlay is None:
            if isinstance(overlay, list):
                for each in overlay:
                    t.add_overlay(each, cmap=plotting.cm.red_transparent)
            else:
                t.add_overlay(overlay, cmap=plotting.cm.red_transparent)
