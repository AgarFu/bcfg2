# This is the bcfg2 support for blastwave packages (pkg-get)
'''This provides bcfg2 support for blastwave'''
__revision__ = '$Revision$'

import Bcfg2.Client.Tools.SYSV, tempfile

class Blast(Bcfg2.Client.Tools.SYSV.SYSV):
    '''Support for Blastwave packages'''
    pkgtype = 'blast'
    pkgtool = ("/opt/csw/bin/pkg-get install %s", ("%s", ["bname"]))
    name = 'Blast'
    __execs__ = ['/opt/csw/bin/pkg-get', "/usr/bin/pkginfo"]
    __handles__ = [('Package', 'blast')]
    __ireq__ = {'Package': ['name', 'version', 'bname']}

    def __init__(self, logger, setup, config):
        # dont use the sysv constructor
        Bcfg2.Client.Tools.PkgTool.__init__(self, logger, setup, config)
        noaskfile = tempfile.NamedTemporaryFile()
        self.noaskname = noaskfile.name
        try:
            noaskfile.write(Bcfg2.Client.Tools.SYSV.noask)
        except:
            pass

    # VerifyPackage comes from Bcfg2.Client.Tools.SYSV
    # Install comes from Bcfg2.Client.Tools.PkgTool
    # Extra comes from Bcfg2.Client.Tools.Tool
    # Remove comes from Bcfg2.Client.Tools.SYSV

    def FindExtraPackages(self):
        '''Pass through to null FindExtra call'''
        return []
