import Bcfg2.Server.Plugin
import Bcfg2.Server.Reports.importscript
from Bcfg2.Server.Reports.reports.models import Client
import lxml.etree, time

class DBStats(Bcfg2.Server.Plugin.StatisticsPlugin):
    __name__ = 'DBStats'
    __version__ = '$Id: $'

    def __init__(self, core, datastore):
        self.cpath = "%s/Metadata/clients.xml" % datastore
        self.core = core

    def StoreStatistics(self, mdata, xdata):
        newstats = xdata.find("Statistics")
        newstats.set('time', time.asctime(time.localtime()))
        e = lxml.etree.Element('Node', name=mdata.hostname)
        e.append(newstats)
        container = lxml.etree.Element("ConfigStatistics")
        container.append(e)
        
        # FIXME need to build a metadata interface to expose a list of clients
        Bcfg2.Server.Reports.importscript.load_stats(
            self.core.metadata.clientdata, container, 0, True)

    def GetExtra(self, client):
        c_inst = Client.objects.filter(name=client)[0]
        return [(a.kind, a.name) for a in
                c_inst.current_interaction.extra_items.all()]

