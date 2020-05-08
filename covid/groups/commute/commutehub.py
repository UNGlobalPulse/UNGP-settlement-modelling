import numpy as np
import pandas as pd
from scipy import spatial
import matplotlib.pyplot as plt

from commutecity import CommuteCity, CommuteCities


class CommuteHub:

    def __init__(self, commutehub_id, lat_lon, city):
        self.id = commutehub_id
        self.lat_lon
        self.city = city # station the hub is affiliated to
        self.passengers = [] # passengers flowing through commute hub
        self.commuteunits = []

class CommuteHubs:

    def __init__(self, commutecities):
        self.commutecities = commutecities
        self.msoa_coordinates = msoa_coordinates
        self.members = []

        self.init_hubs()

    def _get_msoa_lat_lon(self, msoa):

        msoa_lat = float(self.msoa_coordinates['Y'][self.msoa_coordinates['MSOA11CD'] == msoa])
        msoa_lon = float(self.msoa_coordinates['X'][self.msoa_coordinates['MSOA11CD'] == msoa])

        return [msoa_lat, msoa_lon]
            
    def init_hubs(self):
        
        ids = 0
        for commutecity in self.commutecities:
            metro_centroid = commutecity.metro_centroid
            metro_msoas = commutecity.metro_msoas
            metro_msoas_lat_lon = []
            for msoa in metro_msoas:
                metro_msoas_lat_lon.append(self._get_msoa_lat_lon(msoa))

            distances = spatial.KDTree(metro_msoas_lat_lon).query(metro_centroid,len(metro_msoas_lat_lon))[0]
            distance_max = np.max(distances)

            # add fixed offsewt of 0.005
            distance_away = distance_max += 0.005

            # handle London separately
            # give London 8 hubs
            if commutecity.city == 'London':
                # for now give London 4 hubs, but correct this later

                hubs = np.zeros(4*2).reshape(4,2)
                hubs[:,0] = metro_centroid[0]
                hubs[:,1] = metro_centroid[1]

                hubs[0][1] += distance_away
                hubs[1][1] -= distance_away
                hubs[2][0] += distance_away
                hubs[3][0] -= distance_away
                
            # give non-London stations hubs
            else:
                hubs = np.zeros(4*2).reshape(4,2)
                hubs[:,0] = metro_centroid[0]
                hubs[:,1] = metro_centroid[1]

                hubs[0][1] += distance_away
                hubs[1][1] -= distance_away
                hubs[2][0] += distance_away
                hubs[3][0] -= distance_away

            for hub in hubs:
                commute_hub = CommuteHub(
                    commutehub_id = ids,
                    lat_lon = hub,
                    city = commutecity.city
                )

                ids += 1
                
                self.members.append(commute_hub)
            