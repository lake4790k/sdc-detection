from Common import *
from Config import Config


class FindCars:

    def __init__(self, cfg: Config, svc, X_scaler, scale):
        self.cfg = cfg
        self.svc = svc
        self.X_scaler = X_scaler
        self.scale = scale

    def find_cars(self, img):
        #img = img.astype(np.float32) / 255
        cfg = self.cfg

        img_tosearch = img[cfg.y_start:cfg.y_stop, :, :]
        ctrans_tosearch = convert_color(img_tosearch, cfg)
        if self.scale != 1:
            imshape = ctrans_tosearch.shape
            ctrans_tosearch = cv2.resize(ctrans_tosearch, (np.int(imshape[1] / self.scale),
                                                           np.int(imshape[0] / self.scale)))

        ch1 = ctrans_tosearch[:, :, 0]
        ch2 = ctrans_tosearch[:, :, 1]
        ch3 = ctrans_tosearch[:, :, 2]

        nxblocks = (ch1.shape[1] // cfg.pix_per_cell) - cfg.cell_per_block + 1
        nyblocks = (ch1.shape[0] // cfg.pix_per_cell) - cfg.cell_per_block + 1

        window = 8 * 8
        nblocks_per_window = (window // cfg.pix_per_cell) - cfg.cell_per_block + 1
        cells_per_step = 2  # Instead of overlap, define how many cells to step
        nxsteps = (nxblocks - nblocks_per_window) // cells_per_step
        nysteps = (nyblocks - nblocks_per_window) // cells_per_step

        hogs = []
        if cfg.hog_channel == 'ALL':
            hogs.append(get_hog_features(ch1, cfg.orient, cfg.pix_per_cell,
                                         cfg.cell_per_block, feature_vec=False))
            hogs.append(get_hog_features(ch2, cfg.orient, cfg.pix_per_cell,
                                         cfg.cell_per_block, feature_vec=False))
            hogs.append(get_hog_features(ch3, cfg.orient, cfg.pix_per_cell,
                                         cfg.cell_per_block, feature_vec=False))
        else:
            hogs.append(get_hog_features(ctrans_tosearch[:, :, cfg.hog_channel], cfg.orient,
                                         cfg.pix_per_cell, cfg.cell_per_block, feature_vec=False))

        bboxes = []
        for xb in range(nxsteps):
            for yb in range(nysteps):
                ypos = yb * cells_per_step
                xpos = xb * cells_per_step

                if cfg.hog_channel == 'ALL':
                    hog_feat1 = hogs[0][ypos:ypos + nblocks_per_window,
                                    xpos:xpos + nblocks_per_window].ravel()
                    hog_feat2 = hogs[0][ypos:ypos + nblocks_per_window,
                                    xpos:xpos + nblocks_per_window].ravel()
                    hog_feat3 = hogs[0][ypos:ypos + nblocks_per_window,
                                    xpos:xpos + nblocks_per_window].ravel()
                    hog_features = np.hstack((hog_feat1, hog_feat2, hog_feat3))
                else:
                    hog_features = hogs[0][ypos:ypos + nblocks_per_window,
                                            xpos:xpos + nblocks_per_window].ravel()

                xleft = xpos * cfg.pix_per_cell
                ytop = ypos * cfg.pix_per_cell

                subimg = cv2.resize(ctrans_tosearch[ytop:ytop + window, xleft:xleft + window], (64, 64))

                spatial_features = bin_spatial(subimg, size=cfg.spatial_size)
                hist_features = color_hist(subimg, nbins=cfg.hist_bins)

                features = np.hstack((spatial_features, hist_features, hog_features))
                features = features.reshape(1, -1)
                test_features = self.X_scaler.transform(features)
                is_car = self.svc.predict(test_features)

                if is_car == 1:
                    xbox_left = np.int(xleft * self.scale)
                    ytop_draw = np.int(ytop * self.scale)
                    win_draw = np.int(window * self.scale)
                    top_left = (xbox_left, ytop_draw + cfg.y_start)
                    bottom_right = (xbox_left + win_draw, ytop_draw + win_draw + cfg.y_start)
                    bboxes.append((top_left, bottom_right))

        return bboxes

    def draw_cars(self, img):
        bboxes = self.find_cars(img)
        draw_img = np.copy(img)
        color = (0, 0, 255)
        width = 6
        for bbox in bboxes:
            cv2.rectangle(draw_img, bbox[0], bbox[1], color, width)

        return draw_img