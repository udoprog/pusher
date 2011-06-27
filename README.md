About Pusher
===
Hello

Pusher is a simple project manage project deployment into a big environment.
the only requirement on the deployed to servers are ssh with sftp enabled and tar.

It creates a document structure on the remote server similar to capistrano, but
should be extendible to any type of project requiring deployment to one or many
different kinds of servers and environments.

The compact syntax is also suitable to bundle with the project, since the
descriptor only uses one file.

Install
===

    sh> sudo python setup.py install

Pusher depends on.

 * Paramiko
   - python-crypto
 * pyyaml

These should be installed using setup.py, but you never know with the different
types of setup available.

QuickStart
===
Given the following configuration:

    servers:
      s1:
        address: "127.0.0.1"
        server_root: "/opt/quickstart"

    modules:
      quick:
        urls:
          - "file://{root}/quickstart.txt"

    deploys:
      dev:
        servers: [s1]
        modules: [quick]
        checks: []

    checks: {}

    config:
      log_level: ERROR
      ssh_username: "myuser"
      ssh_password: "mypassword"

run.

Create the deploy repo.

    sh> sudo mkdir /opt/quickstart; sudo chown myuser /opt/quickstart

Setup basic configuration.

    sh> pusher setup dev

    Setting up module quick at 127.0.0.1 (s1)

    sh> pusher update dev 1.0

    quick-1.0 new /home/udoprog/repo/git/pusher/.archive/1.0-dev-quick
    quick-1.0 adding file:///home/udoprog/repo/git/pusher/quickstart.txt
    quick-1.0 saving
    quick-1.0 closing

    sh> pusher deploy dev 1.0

    Deploying module quick (version 1.0-dev) to 127.0.0.1 (s1) at /opt/quickstart

    sh> pusher checkout dev 1.0

    Downloading rollback states
    Checking out module quick (version dev-1.0) on 127.0.0.1 (s1)


This will have created the following structure under /opt/quickstart.

    /opt/quickstart/
    /opt/quickstart/quick
    /opt/quickstart/quick/current -> releases/1.0-dev
    /opt/quickstart/quick/releases
    /opt/quickstart/quick/releases/1.0-dev.tar
    /opt/quickstart/quick/releases/1.0-dev
    /opt/quickstart/quick/releases/1.0-dev/quickstart.txt
    /opt/quickstart/quick/revision
    /opt/quickstart/.pusher

Configuration
===

The main configuration file for pusher is the "pusher.yaml" file, it describes
how to collect all resources which are to be deployed, and where they are to
be uploaded.

The following is an example configuration which is located at *pusher.yaml* in
the project directory.

    archive: .archive

    servers:
      s1:
        address: "host1.dev.local"
        server_root: "/opt/deploy"
      s2:
        address: "host2.dev.local"
        server_root: "/opt/deploy"

    modules:
      "core-local":
        before_update: "build now"
        after_checkout: "/etc/init.d/service restart"

        urls:
          - "file://{root}/module/build/deploy.zip"
          - "sftp://resources.dev.local/usr/local/share/resource.txt"
          - "https://example.com/"

    deploys:
      dev:
        servers: [s1, s2]
        modules: [core-local]

    config:
      log_level: ERROR

Using the above, the following commands deploy the project.

**Setup**

    sh> pusher setup dev

This will setup the following structure.

 * /opt/deploy
 * /opt/deploy/dev
 * /opt/deploy/dev/revision (empty file)
 * /opt/deploy/dev/releases/ (empty directory)

**Update**

    sh> pusher update dev 1.0

Update the local archive and download the required files for all associated
modules, prepare version 1.0 for deploy.

Before the update, the command "build now" is executed.

This will create a tar file in *{root}/.archive/core-local-1.0* that contains the following.

 * deploy.zip *downloaded from* "file://{root}/module/build/deploy.zip"
 * resource.txt *downloaded from* "sftp://resources.dev.local/usr/local/share/resource.txt"
 * index.html *downloaded from* "https://example.com/"

*Note: even local file copies are called "downloads" since handle types are not
distinguished.*

**Deploy**

    sh> pusher deploy dev 1.0

Deploy version 1.0 to the dev environment.
This will update and create the following directories:

 * /opt/deploy/dev/releases/core-local-1.0.tar
 * /opt/deploy/dev/releases/core-local-1.0/

**Checkout**

    sh> pusher checkout dev 1.0

Checkout version 1.0 in the deploy environment, this will only change symlinks
and fire triggers. Rollback is applied if anything is unsuccessful.

This will create a symlink to current (or re-create one if something is already
checked out).

  - /opt/deploy/dev/current -> /opt/deploy/dev/releases/core-local-1.0/
  - /opt/deploy/dev/revision (contains "1.0")

Done!

About the format
===

Most fields can use standard python formatting placeholders, i.e. *{name}*.
By default, the current environment is loaded into this configuration, along
with anything specified under *config* and on each separate module.

All dictionary keys are automatically defined as *name*, meaning the following
is a valid server definition:

    servers:
      s1:
        address: "{name}"

**Recursion can never happen** since the dictionary used for formatting is always
a copy of the source, meaning that the following will not work as expected:

    servers:
      s1:
        address: "dev.{network}"
        network: "local.{domain}"
        domain: "example.com"

*address* would simply be expanded to _dev.local.{domain}_, this might be fixed
in the future.

**Variables are scoped**, variables defined under *root > config* will be
globally available for all components (servers/modules/checks), but variables
can also be defined in each separate component definition.

**The schema validates on dictionaries**, meaning that any serialization format
should be acceptable as input for pusher, as long as it can be gracefully
converted into a python dict and supports usual types such as booleans, lists
and string.

**Everything can be configured**, as long as it's documented :-), seriously,
most functions are configurable, adding new commands and handles is dead
simple, just check out the IHandle and ICommand (zope) interfaces.

Special Variables
---

There are some special variables available in the configuration file.

 * *root* Is the directory in which the pusher.yaml configuration is located,
   which is very useful for development deploys which are probably built from
   the directory and not some build server..
 * *version* Is the version currently being deployed, only available where
   applicable.
 * *stage* Is the stage currently being deployed, only available where
   applicable.

Handles
===

The interface that each type of scheme implements is the IHandle interface.

File sources are specified as **urls** under the module component, they have
the format **\<scheme\>**://**\<netloc\>**/**\<path\>**.

Pusher comes with a couple of bundles handles for the following schemes.

**file**

Download the local file, corresponding to the uri.

**http/https**

Download a remote file using http, redirects and cookies are handled
automatically by default.

Configuration:

 * *(http/https)_user_agent* (default: "Pusher/2.0")
 * *(http/https)_use_cookies* (default: true)
 * *(http/https)_send_version* (default: true)
 * *(http/https)_default_name* (default: "index")

**sftp**

Download a file using sftp, uses the normal ssh configuration variables.

ssh-agent and pageant (windows) works automatically through paramiko, so does your normal *$HOME/.ssh/id\_dsa* authentication.

Configuration:

 * *ssh_timeout* (default: 5) 
 * *ssh_bufsize* (default: 2 ** 20)
 * *ssh_io_sleep* (default: 0.1)
 * *ssh_private_key* If private key is made available, is it as an authentication mechanism. Encrypted keys does not work.
 * *ssh_username*
 * *ssh_password*
