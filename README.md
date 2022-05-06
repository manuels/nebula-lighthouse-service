# Public Nebula VPN Lighthouse Server

## Introduction
This server is a public [Nebula VPN](https://www.defined.net/nebula/) Lighthouse Service. You can use it in case you don’t have a publicly accessible server to run your own Nebula Lighthouse.

## List of Public Nebula Lighthouse Services
See [the project's server list](https://htmlpreview.github.io/?https://github.com/manuels/nebula-lighthouse-service/blob/main/server-list.html) 

## What is a Nebula Lighthouse?

In Nebula, a lighthouse is a Nebula host that is responsible for keeping track of all the other Nebula hosts, and helping them find each other within a Nebula network.

## Quickstart

Follow the steps in Nebula’s [Quick Start tutorial](https://www.defined.net/nebula/quick-start/).

> **Security advice:** When you sign the host keys of your devices (e.g. via `nebula-cert sign -groups my_network`), add all your devices to one group (here `my_network`) to be able to block out the Lighthouse service from the rest of your network. (See section Blocking out the Lighthouse from your network).

If you follow this tutorial, you will create three files:

 - `ca.crt`
 - `lighthouse1.crt`
 - `lighthouse1.key`

Now send a POST request with these three files as parameters to this server (also see [API documentation](/docs/)).
Here is an example of how to do it with curl:

```
$ curl -X POST "http://${this_host}/lighthouse/" -F ca_crt=@./ca.crt -F host_crt=@./lighthouse1.crt -F host_key=@./lighthouse1.key
{'port': 49153}
#        ^^^^^ this port will differ for your request
```

(It is not harmful to run this command several times - it is idempotent.)
Now add this information to your clients’ Nebula configuration file using a section like this one:

```
static_host_map:
    "192.168.100.1": ["${this_host}:49153"]
```

The server returns a JSON-encoded response that contains a port that you can now use as your VPN's Nebula lighthouse.
You can check the status of this service using

```
$ curl -X GET "http://${this_host}/lighthouse/" -F ca_crt=@./ca.crt -F host_crt=@./lighthouse1.crt -F host_key=@./lighthouse1.key
{'running': true, 'port': 49153}
```

> **Security advice:** See the next section to ensure that the lighthouse service cannot access other devices in your VPN.

## Blocking out the Lighthouse from your Network

The lighthouse should not have access to your network, so when signing your host keys you should add all devices (excluding the lighthouse) to one group (here `my_network`), e.g.

```
nebula-cert sign -name "laptop" -ip "192.168.100.5/24" -groups "laptop,my_network"
#                                                                      ^^^^^^^^^^ This is important
```

When you add firewall rules to your Nebula config, always make sure to exclude the lighthouse service like this:

```
firewall:
  outbound:
    # Allow all outbound traffic from this node but to the lighthouse
    - port: any
      proto: any
      group: my_network  # <-- this blocks out the nebula lighthouse
      
  inbound:
    # Allow tcp/443 from any host but the lighthouse
    - port: 443
      proto: tcp
      group: my_network  # <-- this blocks out the nebula lighthouse
```

## How to run a public Lighthouse service?
The public Nebula Lighthouse service is distributed [via snap](https://snapcraft.io/nebula-lighthouse-service). Snap allows for Nebula Lighthouse services to run in a strict confinement. 

Install the service:
```
$ sudo snap install nebula-lighthouse-service
```
Set public webserver port:
```
$ sudo snap set nebula-lighthouse-service webserver.port=80
```

Set available port range for lighthouses (according to private port range in [RFC 6335](https://datatracker.ietf.org/doc/html/rfc6335#section-6)):
```
$ sudo snap set nebula-lighthouse-service min-port=49152
$ sudo snap set nebula-lighthouse-service max-port=65535
```

## Debugging the Service
When you run a Nebula Lighthouse service, there is systemd service with the name `snap.nebula-lighthouse-service.webservice` running and for each served lighthouse a service with the name `snap.nebula-lighthouse-service.lighthouse-$i` (where `i` is an increasing number starting with `0`).

You can check if the services are running using
```
$ sudo systemctl status snap.nebula-lighthouse-service.webservice
$ sudo systemctl status snap.nebula-lighthouse-service.lighthouse-0
```
or check the complete logs using
```
sudo journalctl -u snap.nebula-lighthouse-service.webservice
sudo journalctl -u snap.nebula-lighthouse-service.lighthouse-0
```
