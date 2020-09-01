import h5py
import numpy as np
from typing import List
from june.groups.leisure import (
    Pub,
    Pubs,
    Grocery,
    Groceries,
    Cinema,
    Cinemas,
    SocialVenue,
    SocialVenues,
)
from june.world import World

nan_integer = -999
spec_to_group_dict = {"pubs": Pub, "cinemas": Cinema, "groceries": Grocery}
spec_to_supergroup_dict = {"pubs": Pubs, "cinemas": Cinemas, "groceries": Groceries}

<<<<<<< HEAD
=======
# pubs 
def save_pubs_to_hdf5(pubs: Pubs, file_path: str):
    n_pubs = len(pubs)
    with h5py.File(file_path, "a") as f:
        pubs_dset = f.create_group("pubs")
        ids = []
        coordinates = []
        for pub in pubs:
            ids.append(pub.id)
            coordinates.append(np.array(pub.coordinates, dtype=np.float))
        ids = np.array(ids, dtype=np.int)
        coordinates = np.array(coordinates, dtype=np.float)
        pubs_dset.attrs["n_pubs"] = n_pubs
        pubs_dset.create_dataset("id", data=ids)
        pubs_dset.create_dataset("coordinates", data=coordinates)


def load_pubs_from_hdf5(file_path: str):
    with h5py.File(file_path, "r", libver="latest", swmr=True) as f:
        pubs = f["pubs"]
        pubs_list = []
        n_pubs = pubs.attrs["n_pubs"]
        ids = pubs["id"]
        coordinates = pubs["coordinates"]
        for k in range(n_pubs):
            pub = Pub()
            pub.id = ids[k]
            pub.coordinates = coordinates[k]
            pubs_list.append(pub)
    return Pubs(pubs_list)
>>>>>>> master

def save_social_venues_to_hdf5(social_venues_list: List[SocialVenues], file_path: str):
    with h5py.File(file_path, "a") as f:
        f.create_group("social_venues")
        for social_venues in social_venues_list:
            n_svs = len(social_venues)
            social_venues_dset = f["social_venues"].create_group(social_venues.spec)
            ids = []
            coordinates = []
            super_areas = []
            for sv in social_venues:
                ids.append(sv.id)
                coordinates.append(np.array(sv.coordinates, dtype=np.float))
                if sv.super_area is None:
                    super_areas.append(nan_integer)
                else:
                    super_areas.append(sv.super_area.id)
            ids = np.array(ids, dtype=np.int)
            coordinates = np.array(coordinates, dtype=np.float)
            super_areas = np.array(super_areas, dtype=np.int)
            social_venues_dset.attrs["n"] = n_svs
            social_venues_dset.create_dataset("id", data=ids)
            social_venues_dset.create_dataset("coordinates", data=coordinates)
            social_venues_dset.create_dataset("super_area", data=super_areas)


def load_social_venues_from_hdf5(file_path: str):
    social_venues_dict = {}
    with h5py.File(file_path, "r", libver="latest", swmr=True) as f:
<<<<<<< HEAD
        for spec in f["social_venues"]:
            data = f["social_venues"][spec]
            social_venues = []
            n = data.attrs["n"]
            ids = np.empty(n, dtype=int)
            data["id"].read_direct(ids, np.s_[0:n], np.s_[0:n])
            coordinates = np.empty((n, 2), dtype=float)
            data["coordinates"].read_direct(coordinates, np.s_[0:n], np.s_[0:n])
            for k in range(n):
                social_venue = spec_to_group_dict[spec]()
                social_venue.id = ids[k]
                social_venue.coordinates = coordinates[k]
                social_venues.append(social_venue)
            social_venues_dict[spec] = spec_to_supergroup_dict[spec](social_venues)
        return social_venues_dict
=======
        groceries = f["groceries"]
        groceries_list = []
        n_groceries = groceries.attrs["n_groceries"]
        ids = groceries["id"]
        coordinates = groceries["coordinates"]
        for k in range(n_groceries):
            grocery = Grocery()
            grocery.id = ids[k]
            grocery.coordinates = coordinates[k]
            groceries_list.append(grocery)
    return Groceries(groceries_list)

# cinemas

def save_cinemas_to_hdf5(cinemas: Cinemas, file_path: str):
    n_cinemas = len(cinemas)
    with h5py.File(file_path, "a") as f:
        cinemas_dset = f.create_group("cinemas")
        ids = []
        coordinates = []
        for cinema in cinemas:
            ids.append(cinema.id)
            coordinates.append(np.array(cinema.coordinates, dtype=np.float))
        ids = np.array(ids, dtype=np.int)
        coordinates = np.array(coordinates, dtype=np.float)
        cinemas_dset.attrs["n_cinemas"] = n_cinemas
        cinemas_dset.create_dataset("id", data=ids)
        cinemas_dset.create_dataset("coordinates", data=coordinates)
>>>>>>> master


def restore_social_venues_properties_from_hdf5(
    world: World, file_path: str
):
    first_super_area_id = world.super_areas[0].id
    with h5py.File(file_path, "r", libver="latest", swmr=True) as f:
<<<<<<< HEAD
        for spec in f["social_venues"]:
            social_venues = getattr(world, spec)
            first_social_venue_id = social_venues[0].id
            data = f["social_venues"][spec]
            n = data.attrs["n"]
            ids = np.empty(n, dtype=int)
            data["id"].read_direct(ids, np.s_[0:n], np.s_[0:n])
            super_areas = np.empty(n, dtype=int)
            data["super_area"].read_direct(super_areas, np.s_[0:n], np.s_[0:n])
            for k in range(n):
                social_venue = social_venues[ids[k] - first_social_venue_id]
                super_area = super_areas[k]
                if super_area == nan_integer:
                    super_area = None
                else:
                    super_area = world.super_areas[super_area - first_super_area_id]
                social_venue.super_area = super_area
=======
        cinemas = f["cinemas"]
        cinemas_list = []
        n_cinemas = cinemas.attrs["n_cinemas"]
        ids = cinemas["id"]
        coordinates = cinemas["coordinates"]
        for k in range(n_cinemas):
            cinema = Cinema()
            cinema.id = ids[k]
            cinema.coordinates = coordinates[k]
            cinemas_list.append(cinema)
    return Cinemas(cinemas_list)
>>>>>>> master

