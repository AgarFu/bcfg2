import getpass
import os
import random
import socket
import string
import subprocess
import Bcfg2.Server.Admin
import Bcfg2.Server.Plugin
import Bcfg2.Options

# default config file
config = '''
[server]
repository = %s
plugins = %s

[statistics]
sendmailpath = %s
database_engine = sqlite3
# 'postgresql', 'mysql', 'mysql_old', 'sqlite3' or 'ado_mssql'.
database_name =
# Or path to database file if using sqlite3.
#<repository>/etc/brpt.sqlite is default path if left empty
database_user =
# Not used with sqlite3.
database_password =
# Not used with sqlite3.
database_host =
# Not used with sqlite3.
database_port =
# Set to empty string for default. Not used with sqlite3.
web_debug = True

[communication]
protocol = %s
password = %s
certificate = %s/%s
key = %s/%s
ca = %s/%s

[components]
bcfg2 = %s
'''

# Default groups
groups = '''<Groups version='3.0'>
   <Group profile='true' public='true' default='true' name='basic'>
      <Group name='%s'/>
   </Group>
   <Group name='ubuntu'/>
   <Group name='debian'/>
   <Group name='freebsd'/>
   <Group name='gentoo'/>
   <Group name='redhat'/>
   <Group name='suse'/>
   <Group name='mandrake'/>
   <Group name='solaris'/>
</Groups>
'''

# Default contents of clients.xml
clients = '''<Clients version="3.0">
   <Client profile="basic" pingable="Y" pingtime="0" name="%s"/>
</Clients>
'''

# Mapping of operating system names to groups
os_list = [
           ('Redhat/Fedora/RHEL/RHAS/Centos',   'redhat'),
           ('SUSE/SLES',                        'suse'),
           ('Mandrake',                         'mandrake'),
           ('Debian',                           'debian'),
           ('Ubuntu',                           'ubuntu'),
           ('Gentoo',                           'gentoo'),
           ('FreeBSD',                          'freebsd')
          ]

# Complete list of plugins
plugin_list = ['Account', 'Base', 'Bundler', 'Cfg',
             'Decisions', 'Deps', 'Metadata', 'Packages',
             'Pkgmgr', 'Probes', 'Properties', 'Rules',
             'Snapshots', 'SSHbase', 'Statistics', 'Svcmgr',
             'TCheetah', 'TGenshi']

# Default list of plugins to use
default_plugins = ['SSHbase', 'Cfg', 'Pkgmgr', 'Rules',
                'Metadata', 'Base', 'Bundler']

def gen_password(length):
    """Generates a random alphanumeric password with length characters"""
    chars = string.letters + string.digits
    newpasswd = ''
    for i in range(length):
        newpasswd = newpasswd + random.choice(chars)
    return newpasswd

def create_key(hostname, keypath, certpath):
    """Creates a bcfg2.key at the directory specifed by keypath"""
    kcstr = "openssl req -batch -x509 -nodes -subj '/C=US/ST=Illinois/L=Argonne/CN=%s' -days 1000 -newkey rsa:2048 -keyout %s -noout" % (hostname, keypath)
    subprocess.call((kcstr), shell=True)
    ccstr = "openssl req -batch -new  -subj '/C=US/ST=Illinois/L=Argonne/CN=%s' -key %s | openssl x509 -req -days 1000 -signkey %s -out %s" % (hostname, keypath, keypath, certpath)
    subprocess.call((ccstr), shell=True)
    os.chmod(keypath, 0o600)

def create_conf(confpath, confdata):
    # don't overwrite existing bcfg2.conf file
    if os.path.exists(confpath):
        result = input("\nWarning: %s already exists. "
                    "Overwrite? [y/N]: " % confpath)
        if result not in ['Y', 'y']:
            print(("Leaving %s unchanged" % confpath))
            return
    try:
        open(confpath, "w").write(confdata)
        os.chmod(confpath, 0o600)
    except Exception as e:
        print(("Error %s occured while trying to write configuration "
              "file to '%s'\n" %
               (e, confpath)))
        raise SystemExit(1)


class Init(Bcfg2.Server.Admin.Mode):
    __shorthelp__ = ("Interactively initialize a new repository")
    __longhelp__ = __shorthelp__ + "\n\nbcfg2-admin init"
    __usage__ = "bcfg2-admin init"
    options = {
                'configfile': Bcfg2.Options.CFILE,
                'plugins'   : Bcfg2.Options.SERVER_PLUGINS,
                'proto'     : Bcfg2.Options.SERVER_PROTOCOL,
                'repo'      : Bcfg2.Options.SERVER_REPOSITORY,
                'sendmail'  : Bcfg2.Options.SENDMAIL_PATH,
              }
    repopath = ""
    response = ""
    def __init__(self, configfile):
        Bcfg2.Server.Admin.Mode.__init__(self, configfile)

    def _set_defaults(self):
        """Set default parameters"""
        self.configfile = self.opts['configfile']
        self.repopath = self.opts['repo']
        self.password = gen_password(8)
        self.server_uri = "https://%s:6789" % socket.getfqdn()
        self.plugins = default_plugins

    def __call__(self, args):
        Bcfg2.Server.Admin.Mode.__call__(self, args)

        # Parse options
        self.opts = Bcfg2.Options.OptionParser(self.options)
        self.opts.parse(args)
        self._set_defaults()

        # Prompt the user for input
        self._prompt_config()
        self._prompt_repopath()
        self._prompt_password()
        self._prompt_hostname()
        self._prompt_server()
        self._prompt_groups()

        # Initialize the repository
        self.init_repo()

    def _prompt_hostname(self):
        '''Ask for the server hostname'''
        data = input("What is the server's hostname: [%s]" % socket.getfqdn())
        if data != '':
            self.shostname = data
        else:
            self.shostname = socket.getfqdn()

    def _prompt_config(self):
        """Ask for the configuration file path"""
        newconfig = input("Store bcfg2 configuration in [%s]: " %
                                self.configfile)
        if newconfig != '':
            self.configfile = newconfig

    def _prompt_repopath(self):
        """Ask for the repository path"""
        while True:
            newrepo = input("Location of bcfg2 repository [%s]: " %
                                  self.repopath)
            if newrepo != '':
                self.repopath = newrepo
            if os.path.isdir(self.repopath):
                response = input("Directory %s exists. Overwrite? [y/N]:"\
                                      % self.repopath)
                if response.lower().strip() == 'y':
                    break
            else:
                break

    def _prompt_password(self):
        """Ask for a password or generate one if none is provided"""
        newpassword = getpass.getpass(
                "Input password used for communication verification "
                "(without echoing; leave blank for a random): ").strip()
        if len(newpassword) != 0:
            self.password = newpassword

    def _prompt_server(self):
        """Ask for the server name"""
        newserver = input("Input the server location [%s]: " % self.server_uri)
        if newserver != '':
            self.server_uri = newserver

    def _prompt_groups(self):
        """Create the groups.xml file"""
        prompt = '''Input base Operating System for clients:\n'''
        for entry in os_list:
            prompt += "%d: %s\n" % (os_list.index(entry) + 1, entry[0])
        prompt += ': '
        while True:
            try:
                self.os_sel = os_list[int(input(prompt))-1][1]
                break
            except ValueError:
                continue

    def _prompt_plugins(self):
        default = input("Use default plugins? (%s) [Y/n]: " % ''.join(default_plugins)).lower()
        if default != 'y' or default != '':
            while True:
                plugins_are_valid = True
                plug_str = input("Specify plugins: ")
                plugins = plug_str.split(',')
                for plugin in plugins:
                    plugin = plugin.strip()
                    if not plugin in plugin_list:
                        plugins_are_valid = False
                        print("ERROR: plugin %s not recognized" % plugin)
                if plugins_are_valid:
                    break

    def _init_plugins(self):
        # Initialize each plugin-specific portion of the repository
        for plugin in self.plugins:
            if plugin == 'Metadata':
                Bcfg2.Server.Plugins.Metadata.Metadata.init_repo(self.repopath, groups, self.os_sel, clients)
            else:
                try:
                    module = __import__("Bcfg2.Server.Plugins.%s" % plugin, '',
                                        '', ["Bcfg2.Server.Plugins"])
                    cls = getattr(module, plugin)
                    cls.init_repo(self.repopath)
                except Exception as e:
                    print('Plugin setup for %s failed: %s\n Check that dependencies are installed?' % (plugin, e))

    def init_repo(self):
        '''Setup a new repo'''
        # Create the contents of the configuration file
        keypath = os.path.dirname(os.path.abspath(self.configfile))
        confdata = config % (
                        self.repopath,
                        ','.join(self.opts['plugins']),
                        self.opts['sendmail'],
                        self.opts['proto'],
                        self.password,
                        keypath, 'bcfg2.crt',
                        keypath, 'bcfg2.key',
                        keypath, 'bcfg2.crt',
                        self.server_uri
                    )

        # Create the configuration file and SSL key
        create_conf(self.configfile, confdata)
        kpath = keypath + '/bcfg2.key'
        cpath = keypath + '/bcfg2.crt'
        create_key(self.shostname, kpath, cpath)

        # Create the repository
        path = "%s/%s" % (self.repopath, 'etc')
        os.makedirs(path)
        self._init_plugins()
        print("Repository created successfuly in %s" % (self.repopath))
