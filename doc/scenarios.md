# Common Scenarios

This document describes the most common used *IPSEC* scenarios and their corresponding configuration parameters.

## Site-to-site using psk

Example of site-to-site connection with explanations

```yaml
connections:
  ikev1-psk-xauth: # name of the connection
    version: 2 # ike version
    remote_addrs: 192.0.2.1
    # proposed algorithms to use for ike cipher containing of one symmetric cipher algorithm,
    # one hash algorithm and one diffie hellman group #TODO
    proposals: aes256gcm16-prfsha384-ecp384
    # add virtual addresses to requests
    vips: '0.0.0.0,::'
    # parameters for local side authentication
    # it is possible to configure multiple rounds of configuration
    local-1:
      # id of local side used for authentication round
      id: 'leftside.example.com'
      auth: psk
    local-2:
      auth: psk
      # parameters of remote side
      id: 'leftside2.example.com'
    remote-1:
      auth: psk
      # You might have to set this to the correct value, if external ip address of remote shall not be used
      id: 'rightside.example.com'
    
    ## each IKE connection can contain multiple children security associations (CHILD_SA)
    children:
      ikev1-psk-xauth: # name of the connection
        # traffic selector for the left (local) site
        # multiple traffic selectors can be entered as a comma seperated list
        # use of the word `dynamic` will use the outer tunnel address,
        # which might be the IP in the range of the default route
        local_ts: '203.0.113.0/24'
        # traffic selector for the remote site
        remote_ts: '0.0.0.0/0,::/0'
        # mode to use
        mode: tunnel
        # proposal for the child-ca
        esp_proposals: aes256gcm16-prfsha384-ecp384
        # action to take when configuration is loaded
        # none: (default) connection has to be connected manually or is waiting for the other side
        # trap: will connect as soon as traffic is trying to use the connection
        # start: initiates the connection actively
        start_action: trap
        # action to take when dead peer is detected
        # clear: (default) just clears the CHILD_SA
        # trap: installs a trap to reconnect when new traffic is detected
        # restart: tries to restart CHILD_SA immediately
        
secrets:
  # PSK secret with name `ike<suffix>`
  ike-connection-1:
    # PSK secret itself
    secret: "CorrectHorseBatteryStaple"
    # IDs of the corresponding peers with name `id<suffix>`
    id-1: 'leftside.example.com'
    id-2: 'rightside.example.com'
```
