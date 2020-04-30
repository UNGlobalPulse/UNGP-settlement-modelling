from covid.groups import Group


class Hospital(Group):
    """
    The Hospital class represents a hospital and contains information about 
    its patients and workers - the latter being the usual "people".

    TODO: we have to figure out the inheritance structure; I think it will
    be an admixture of household and company.
    I will also assume that the patients cannot infect anybody - this may
    become a real problem as it is manifestly not correct.
    """

    def __init__(self, hospital_id=1, structure=None, area=None):
        super().__init__("Hospital_%03d" % hospital_id, "hospital")
        self.id = hospital_id
        self.area = area
        self.patients = []
        self.ICUpatients = []
        """
        I foresee that we get information about beds/ICU beds etc.
        into the composition
        """
        self.hospital_structure = structure
        print("I am Boris - this is my virtual hospital", self.id)

    def set_active_members(self):
        for person in self.people:
            if person.active_group is None:
                person.active_group = "hospital"

    def add_as_patient(self, person):
        self.patients.append(person)

    def update_status_lists(self):
        print("=== update status list for hospital with ", len(self.people), " people ===")
        print("=== hospital currently has ", len(self.patients), " patients =============")
        super().update_status_lists()
        for patient in self.patients:
            patient.health_information.update_health_status()


class Hospitals:
    """
    Contains all hospitals for the given area, and information about them.
    """

    def __init__(self, world, box_mode=False):
        self.world = world
        self.box_mode = box_mode
        self.members = []
        # self.hospital_trees = self._create_hospital_tree(hospital_df)
        if self.box_mode:
            self.members.append(Hospital())

    def get_nearest(self, person):
        if self.box_mode:
            return self.members[0]

    # def _create_hospital_tree(self,hospital_df):
    #    hospital_tree = BallTree(
    #        np.deg2rad(hospital_df[["Latitude", "Longitude"]].values), metric="haversine"
    #        )
    #    return hospital_tree

    # def get_closest_hospital(self,area,k):
    #    hospital_tree = self.hospital_trees
    #    distances,neighbours = hospital_tree.query(
    #        np.deg2rad(area.coordinates.reshape(1,-1)),k = k,sort_results=True
    #        )
    #    return neighbours
