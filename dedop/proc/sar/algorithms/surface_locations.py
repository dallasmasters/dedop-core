import numpy as np


from ...geo import lla2ecef, ecef2lla
from ..base_algorithm import BaseAlgorithm
from ...functions import *

class SurfaceLocationAlgorithm(BaseAlgorithm):
    def __init__(self, chd, cst):
        self.first_surf = False
        self.new_surf = False

        self.time_surf = 0
        self.x_surf = 0
        self.y_surf = 0
        self.z_surf = 0
        self.lat_surf = 0
        self.lon_surf = 0
        self.alt_surf = 0

        super().__init__(chd, cst)

    def get_surface(self):
        return {
            'time_surf': self.time_surf,
            'x_surf': self.x_surf,
            'y_surf': self.y_surf,
            'z_surf': self.z_surf,
            'lat_surf': self.lat_surf,
            'lon_surf': self.lon_surf,
            'alt_surf': self.alt_surf
        }

    def store_first_location(self, isps):
        isp_record = isps[-1]

        self.time_surf = isp_record.time_sar_ku

        # self.x_surf = isp_record.x_sar_surf
        # self.y_surf = isp_record.y_sar_surf
        # self.z_surf = isp_record.z_sar_surf

        self.lat_surf = isp_record.lat_sar_sat
        self.lon_surf = isp_record.lon_sar_sat
        self.alt_surf = isp_record.alt_sar_sat -\
                        isp_record.win_delay_sar_ku * self.cst.c / 2.

        surf = lla2ecef(
            [self.lat_surf, self.lon_surf, self.alt_surf], self.cst
        )
        self.x_surf = surf[0]
        self.y_surf = surf[1]
        self.z_surf = surf[2]

    def __call__(self, locs, isps):
        if not locs:
            self.first_surf = True
            self.new_surf = True

            self.store_first_location(isps)
        else:
            self.first_surf = False
            self.new_surf = self.find_new_location(locs, isps)
        return self.new_surf

    def find_new_location(self, locs, isps):
        surface = locs[-1]
        isp_curr = isps[-1]
        isp_prev = isps[-2]

        ground_surf_orbit_vector = np.matrix(
            [[isp_curr.x_sar_surf - surface.x_sat],
             [isp_curr.y_sar_surf - surface.y_sat],
             [isp_curr.z_sar_surf - surface.z_sat]],
            dtype=np.float64
        )
        ground_surf_orbit_angle = angle_between(
            surface.surf_sat_vector, ground_surf_orbit_vector
        )
        if ground_surf_orbit_angle < surface.angular_azimuth_beam_resolution:
            return False

        ground_surf_orbit_vector_prev = np.matrix(
            [[isp_prev.x_sar_surf - surface.x_sat],
             [isp_prev.y_sar_surf - surface.y_sat],
             [isp_prev.z_sar_surf - surface.z_sat]],
            dtype=np.float64
        )
        ground_surf_orbit_angle_prev = angle_between(
            surface.surf_sat_vector, ground_surf_orbit_vector_prev
        )

        # compute alpha - the ratio of the position of the surface
        #   between the two ISP readings
        alpha = (surface.angular_azimuth_beam_resolution - ground_surf_orbit_angle_prev) /\
                (ground_surf_orbit_angle - ground_surf_orbit_angle_prev)

        self.time_surf = isp_prev.time_sar_ku +\
            alpha * (isp_curr.time_sar_ku - isp_prev.time_sar_ku)
        self.x_surf = isp_prev.x_sar_surf +\
            alpha * (isp_curr.x_sar_surf - isp_prev.x_sar_surf)
        self.y_surf = isp_prev.y_sar_surf +\
            alpha * (isp_curr.y_sar_surf - isp_prev.y_sar_surf)
        self.z_surf = isp_prev.z_sar_surf +\
            alpha * (isp_curr.z_sar_surf - isp_prev.z_sar_surf)

        surf_loc_cart = np.array([self.x_surf,
                                  self.y_surf,
                                  self.z_surf])
        surf_loc_geod = ecef2lla(surf_loc_cart, self.cst)
        self.lat_surf = surf_loc_geod[0][0, 0]
        self.lon_surf = surf_loc_geod[1][0, 0]
        self.alt_surf = surf_loc_geod[2][0, 0]

        return True