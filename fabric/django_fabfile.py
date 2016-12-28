# Deploy Drupal code from the repository to the application servers.
# Intended to run as a deployment script on a Jenkins server. 

from fabric.api import *
import logging

logging.getLogger('paramiko.transport').addHandler(logging.StreamHandler())

# Deploy with the Jenkins user.
env.user                = 'jenkins'
env.key_filename        = ['/var/lib/jenkins/.ssh/key1.rsa','/var/lib/jenkins/.ssh/key2.rsa',]

# Support for nonstandard symlinks between applications.
# if no extra links are defined, we pass over the deployment step.
# If extra links are defined, we symlink them before the build.
# Useful if the developers symlinked 2 django virtualenvs together.

extraLinks = 'pass'
# Default Code Branch
codeBranch = 'AWS'

# Django App: app1
@task
@hosts('localhost')
def commitmentrequestapp():
  global appName
  global appRepo
  global appSource
  appName       = 'app1'
  appRepo       = 'git@github.com:someexample/app1.git'
  appSource     = 'app1POC'

# Django App: app2
@task
@hosts('localhost')
def app2():
  global appName
  global appRepo
  global appSource
  global extraLinks
  global linkDest
  appName       = 'app2'
  appRepo       = 'git@github.com:someexample/app2.git'
  appSource     = 'app2POC'
  extraLinks    = ['directory1','directory2','directory3']
  linkDest      = '/var/venv/app1'
###### Environment Variables ######
@task
@hosts('localhost')
def app1_aws():
  global codeBranch
  env.hosts     = [
                  ]
  codeBranch   = "AWS"
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
        local("git checkout origin/%s" % codeBranch)
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

# create relevant symlinks for the App.
@parallel
def code_link():
    with settings(warn_only=True):
        run("rm %s/source" % appDir)
        run("ln -s %s/releases/%s %s/source" % (appDir, revNum, appDir))
        run("ln -sf %s/private/local_settings.py %s/source/%s/local_settings.py" % (appDir, appDir, appSource))
        run("ln -s /etc/newrelic/newrelic.ini %s/source/newrelic.ini" % appDir)

@parallel
def extra_link():
    if extraLinks != 'pass':
      with settings(warn_only=True):
        for link in extraLinks:
          run("ln -s %s/source/%s %s/source/%s" % (linkDest, link, appDir, link))
  
# Execute build for Django App.
@parallel
def django_build():
      run("%s/bin/pip install -r %s/source/requirements.txt" % (appDir, appDir))

@parallel
def django_migrate():
      run("%s/bin/python %s/source/manage.py collectstatic --noinput" % (appDir, appDir))
      run("%s/bin/python %s/source/manage.py migrate" % (appDir, appDir))

# Restart services so that Drupal picks up the changed code.
def restart_services():
     sudo('/usr/sbin/service uwsgi-emperor reload')

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
  appDir        = ("/var/venv/%s" % appName)
  repoCache     = ("/var/tmp/repositories/%s" % appName)
  execute(code_fetch)
  execute(code_pack)
  execute(code_ship)
  execute(code_link)
  execute(extra_link)
  execute(django_build)
  runs_once(django_migrate) # Don't 'collectstatic' and 'migrate' from every host.
  execute(restart_services)
  execute(cleanup_remote)
  execute(cleanup_local)
