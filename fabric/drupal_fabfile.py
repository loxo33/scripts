# Deploy Drupal code from the repository to the application servers.
# Usage Consists of 3 sections:
# drupal_fabfile.py <Drupal App> <Environment> deploy
# The first 2, <Drupal App> and <Environment> set global variables
# which are application and environment-specific. 
# the final task, "deploy," invokes the deployment function.
 
from fabric.api import *
import logging

logging.getLogger('paramiko.transport').addHandler(logging.StreamHandler())

USER = 'jenkins'
KEY  = '/var/lib/jenkins/id_rsa'

# Deploy with the Jenkins user. Support for multiple keys with array.
env.user		= 'jenkins'
env.key_filename	= ['/var/lib/jenkins/.ssh/key1.rsa','/var/lib/jenkins/.ssh/key2.rsa',]

###### Drupal App ######
# This section changes between each Drupal site. 

# Drupal Site: app1.example.org
@task
@hosts('localhost')
def app1():
  global appName
  global appRepo
  global appFiles
  appName       = 'app1.example.org'
  appRepo       = 'git@github.com:somerepo/app1.git'
  appFiles	= 'current/sites/default/files'

# Drupal Site: app2.example.org
@task
@hosts('localhost')
def app2():
  global appName
  global appRepo
  global appFiles
  global KEY
  appName       = 'app2.example.org'
  appRepo       = 'git@git.assembla.com:somerepo_app2_website.git'
  appFiles      = 'current/sites/default/files'
  KEY           = '/var/lib/jenkins/.ssh/jenkins_key2.rsa'

###### Environment Variables ######
@task
@hosts('localhost')
def test():
  global realmDomain
  global realmBranch
  env.hosts	= ['12.34.56.789',]
  realmDomain	= 'example.org'
  realmBranch	= 'master'

@task
@hosts('localhost')
def app1_prod():
  global realmBranch
  env.hosts     = ['app1.us-west-2.compute.internal',]
  realmBranch   = 'master'

@task
@hosts('localhost')
def app2_aws():
  global realmBranch
  env.hosts     = ['web1.us-west-2.compute.internal',
	           'web2.us-west-2.compute.internal',
                  ]
  realmBranch   = 'PROD'

###### Deployment Functions ######
# Get the most updated code from the upstream
# repository and cache it locally. 
@hosts('localhost')
def code_fetch():
    global revNum
    with settings(warn_only=True):
        if local("test -d %s" % repoCache).failed:
            local("mkdir -p %s" % repoCache)
            local("git clone %s %s" % (appRepo, repoCache))
    with lcd(repoCache):
        local("git fetch origin")
	local("git checkout origin/%s" % realmBranch)
    revNum = local('git --git-dir %s/.git rev-parse --short=10 HEAD' % repoCache, capture=True)

@hosts('localhost')
def code_pack():
    # tar the code
    local('tar czf /tmp/deploy_%s.tar.gz -C %s .' % (revNum, repoCache))

@parallel
def code_ship():
    # put (sftp) tarball to remote app server.
    put("/tmp/deploy_%s.tar.gz" % revNum, "/tmp")
    # untar the code into the relevant application directory.
    with settings(warn_only=True):
        if run("test -d %s/releases/%s" % (appDir, revNum)).failed:
            run("mkdir %s/releases/%s" % (appDir, revNum))
        run("tar xzfm /tmp/deploy_%s.tar.gz -C %s/releases/%s" % (revNum, appDir, revNum))

# create relevant symlinks for drupal.
@parallel
def code_link():
    with settings(warn_only=True):
        run("rm %s/current" % appDir)
        run("ln -s %s/releases/%s %s/current" % (appDir, revNum, appDir))
        run("ln -sf %s/private/local.settings.php %s/current/sites/default/local.settings.php" % (appDir, appDir))
        run("ln -nsf %s/files %s/%s" % (appDir, appDir, appFiles))

# Restart services to clear php opcode cache.
def restart_services():
     sudo('/usr/sbin/service php5-fpm restart')
# Keep last 3 deployments, cleanup the rest. 
@parallel
def cleanup_remote():
    with settings(warn_only=True):
        run("ls -1dt %s/releases/* | tail -n +4 |  xargs rm -rf" % appDir)
        run('rm /tmp/deploy_%s.tar.gz' % revNum)

# Remove local files.
@hosts('localhost')
def cleanup_local():
    local('rm /tmp/deploy_%s.tar.gz' % revNum)

### MAIN ###
@task
@hosts('localhost')
def deploy():
  global appDir
  global repoCache
  appDir        = ("/var/www/%s" % appName)
  repoCache	= ("/var/tmp/repositories/%s" % appName)
  execute(code_fetch)
  execute(code_pack)
  execute(code_ship)
  execute(code_link)
  execute(restart_services)
  execute(cleanup_remote)
  execute(cleanup_local)
