About Pusher
===

Pusher is a simple project manage project deployment into a big environment.
the only requirement on the deployed to servers are ssh with sftp enabled and tar.

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
      "core-dev-local":
        after_checkout: "/etc/init.d/service restart"
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
          - core-dev-local
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

Using the above, the following command series will build and deploy the
project.

    #> pusher setup dev

Update the local archive, prepare version 1.0 for deploy.

    #> pusher update dev 1.0

Deploy version 1.0 to the dev environment.

    #> pusher deploy dev 1.0

Checkout version 1.0 in the deploy environment, this will only change symlinks
and fire triggers. Rollback is applied if anything is unsuccessful.

    #> pusher checkout dev 1.0

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
