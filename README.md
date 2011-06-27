About Pusher
===

Pusher is a simple project manage project deployment into a big environment.
the only requirement on the deployed to servers are ssh with sftp enabled and tar.

It creates a document structure on the remote server similar to capistrano, but
should be extendible to any type of project requiring deploy to an upstream
server.

The compact syntax is also suitable to bundle with the project, given that it
only occupies one file.

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

        # multiple source types can be used, these depend on specific
        # configuration variables
        urls:
          - "file://{root}/module/build/deploy.zip"
          - "sftp://resources.dev.local/usr/local/share/resource.txt"
          - "https://example.com/"

    checks:
      Deploy:
        command: "test -d /opt/deploy"
      FindUser:
        command: "grep '^{FindUser}:' /etc/passwd > /dev/null"

    deploys:
      dev:
        servers:
          - s1
          - s2
        modules:
          - core-local
        checks:
          - Deploy
          - FindUser

    config:
      ssh_private_key: "{HOME}/.ssh/id_dsa"
      FindUser: "example"
      log_level: ERROR

      # extra handles
      # this is used by default, but anything derigin pusher.handles.base#IHandle
      can be used
      handles:
        - pusher.handles.file#FileHandle

Using the above, the following commands deploy the project.

    #> pusher setup dev

This will create the following directories.

  - /opt/deploy
  - /opt/deploy/dev
  - /opt/deploy/dev/revision (empty file)
  - /opt/deploy/dev/releases/

    #> pusher update dev 1.0

Update the local archive and download the required files for all associated
modules, prepare version 1.0 for deploy.

Before the update, the command "build now" is executed.

This will create a tar file in *{root}.archive/core-local-1.0* that is ready to
be sent to the server.

    #> pusher deploy dev 1.0

Deploy version 1.0 to the dev environment.
This will update and create the following directories:

  - /opt/deploy/dev/releases/core-local-1.0.tar
  - /opt/deploy/dev/releases/core-local-1.0/

    #> pusher checkout dev 1.0

Checkout version 1.0 in the deploy environment, this will only change symlinks
and fire triggers. Rollback is applied if anything is unsuccessful.

This will create a symlink to current (or re-create one if something is already
checked out).

  - /opt/deploy/dev/current -> /opt/deplot/dev/releases/core-local-1.0/
  - /opt/deploy/dev/revision (contains "1.0")

Done!

Variables
===

Most fields can use standard python formatting placeholders, i.e. *{name}*.
By default, the current environment is loaded into this configuration, along
with anything specified under *config* and on each separate module.

All dictionary keys are automatically defined as *name*, meaning the following
is a valid server definition:

    servers:
      s1:
        address: "{name}"

Recursion can never occur since the dictionary used for formatting is always
a copy of the source, meaning that the following will not work as expected:

    servers:
      s1:
        address: "dev.{network}"
        network: "local.{domain}"
        domain: "example.com"

*address* would simply be expanded to _dev.local.{domain}_, this might be fixed
in the future.

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

IHandle
===

The interface that each type of scheme implements is the IHandle interface.
Pusher comes bundled with handles for the following schemes.

file
---
Download the local file, corresponding to the uri.

http/https
---
Download a remote file using http, redirects and cookies are handled
automatically by default.

Configuration:
  - *(http/https)_user_agent* (default: "Pusher/2.0")
  - *(http/https)_use_cookies* (default: true)
  - *(http/https)_send_version* (default: true)
  - *(http/https)_default_name* (default: "index")

sftp
---
Download a file using sftp, uses the normal ssh configuration variables.

ssh-agent and pageant (windows) works automatically through paramiko, so does your normal .ssh/id\_dsa authentication.

Configuration:
  - *ssh_timeout* (default: 5) 
  - *ssh_bufsize* (default: 2 ** 20)
  - *ssh_io_sleep* (default: 0.1)
  - *ssh_private_key* If private key is made available, is it as an authentication mechanism. Encrypted keys does not work.
  - *ssh_username*
  - *ssh_password*
