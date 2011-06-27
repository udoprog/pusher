About Pusher
===

Pusher is a simple project manage project deployment into a big environment.
the only requirement on the deployed to servers are ssh with sftp enabled and tar.

Configuration
===

The main configuration file for pusher is the "pusher.yaml" file, it describes
how to collect all resources which are to be deployed, and where they are to
be uploaded.

The following is an example configuration:

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
