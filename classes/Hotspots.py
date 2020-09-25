from utils import load_hotspots, api_call


class Hotspots:

    def __init__(self, force=False):
        """
        Interface for easily finding hotspots
        :param force: Force reload hotspots
        """
        self.hotspots = load_hotspots(force)

        self.hspot_by_addr = dict()
        self.hspot_by_name = dict()  # note there are already name collisions use at your own risk
        for h in self.hotspots:
            self.hspot_by_addr[h['address']] = h
            self.hspot_by_name[h['name'].lower()] = h

    def get_hotspot_by_addr(self, address):
        return self.hspot_by_addr.get(address)

    def get_hotspot_by_name(self, name):
        return self.hspot_by_name.get(name.lower())

    def get_hotspots_by_owner(self, owner):
        hspots = []
        for h in self.hotspots:
            if h['owner'] == owner:
                hspots.append(h)
        return h


    def get_hotspot_witnesses(self, address=None, name=None):
        h = None
        if name:
            h = self.get_hotspot_by_name(name)
        else:
            h = self.get_hotspot_by_addr(address)
        w = api_call(path=f"hotspots/{h['address']}/witnesses")
        return w.get('data')

    def get_hotspots(self):
        return self.hotspots
