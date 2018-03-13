#!/bin/sh
set -eo pipefail

_initialize_single() {
    echo "Start: run initializations."
    _create_vti ""
    echo "End: run initializations."
}

_initialize_multi() {
    for i in $(seq $IPSEC_NUMCONF);
    do
        _create_vti "CONFIGS_${i}_"
    done
}


_create_vti(){

# set charon.install_virtual_ip = no to prevent the daemon from also installing the VIP

eval    if [ -n "\$IPSEC_${1}VTI_KEY" ]; then
eval        echo "IPSEC_VTI_KEY set, creating VTI interface."
        set -e

        echo "Start: load ip_vti kernel module."
        if grep -qe "^ip_vti\>" /proc/modules; then
          echo "VTI module already loaded."
        else
          echo "Loading VTI module."
          modprobe ip_vti || true
        fi
        echo "End: load ip_vti kernel module."

eval        VTI_IF="vti${IPSEC_VTI_KEY}"

eval        ip tunnel add "${VTI_IF}" remote ${IPSEC_REMOTEIP} mode vti key ${IPSEC_VTI_KEY} || true
        ip link set "${VTI_IF}" up

        # add routes through the VTI interface
eval        if [ -n "\$IPSEC_${1}VTI_STATICROUTES" ]; then
            IFS=","
eval            for route in \${IPSEC_${1}VTI_STATICROUTES}; do
                ip route add ${route} dev "${VTI_IF}" || true
            done
            unset IFS
        fi

        # vti interface address configuration
eval        if [ -n "\$IPSEC_${1}VTI_IPADDR_LOCAL" -a -n "\$IPSEC_${1}VTI_IPADDR_PEER" ]; then
eval            echo "Configuring local/peer (\$IPSEC_${1}VTI_IPADDR_LOCAL/\$IPSEC_${1}VTI_IPADDR_PEER) addresses on $VTI_IF."
eval            ip addr add \$IPSEC_${1}VTI_IPADDR_LOCAL peer \$IPSEC_${1}VTI_IPADDR_PEER dev $VTI_IF
        fi

        echo "Setting net.ipv4.conf.${VTI_IF}.disable_policy=1"
        sysctl -w "net.ipv4.conf.${VTI_IF}.disable_policy=1"

    fi
}

_config() {
    echo "======= Create config ======="

    # copies the template to be used
    # different templates might be used in the future depending on
    # configured values
    cp /etc/confd/conf.d.disabled/*.psk-template.* /etc/confd/conf.d
    cp /etc/confd/conf.d.disabled/charon.* /etc/confd/conf.d

    confd -onetime -backend env
    if [ -n "$DEBUG" ]
    then
        echo "======= Config ======="
        cat /etc/ipsec.config.d/*.conf
    fi
}

_start_strongswan() {
    echo "======= start VPN ======="
    set +eo pipefail
    ipsec start --nofork &
    child=$!
    wait "$child"
}

_remove_route() {
    echo "ip route del $IPSEC_REMOTENET via $DEFAULTROUTER dev eth0 proto static src $IPSEC_LOCALPRIVIP"
    ip route del $IPSEC_REMOTENET via $DEFAULTROUTER dev eth0 proto static src $IPSEC_LOCALPRIVIP
    return 0
}

_add_route() {
    echo "======= setup route ======="
    DEFAULTROUTER=`ip route | head -1 | cut -d ' ' -f 3`
    echo "ip route add $IPSEC_REMOTENET via $DEFAULTROUTER dev eth0 proto static src $IPSEC_LOCALPRIVIP"
    ip route add $IPSEC_REMOTENET via $DEFAULTROUTER dev eth0 proto static src $IPSEC_LOCALPRIVIP
}

_term() {
    echo "======= caught SIGTERM signal ======="
    ipsec stop
    if [ -n "$SET_ROUTE_DEFAULT_TABLE" ] && [ "$SET_ROUTE_DEFAULT_TABLE" = "TRUE" ]
    then
        _remove_route
    fi
    exit 0
}

_set_default_variables_single() {
    _set_default_variables ""
}

_set_default_variables_multi() {
    for i in $(seq $IPSEC_NUMCONF);
    do
        eval export IPSEC_${i}_NUM=${i}
        _set_default_variables "CONFIGS_${i}_"
    done
}

_set_default_variables() {
    # local and remote IP can not be "%any" if VTI needs to be created
eval    if [ -z "\$IPSEC_${1}VTI_KEY" ]; then
eval        export IPSEC_${1}LOCALIP=\${IPSEC_${1}LOCALIP:-%any}
    fi
eval    export IPSEC_${1}REMOTEIP=\${IPSEC_${1}REMOTEIP:-%any}
eval    export IPSEC_${1}KEYEXCHANGE=\${IPSEC_${1}KEYEXCHANGE:-ikev2}
eval    export IPSEC_${1}ESPCIPHER=\${IPSEC_${1}ESPCIPHER:-aes192gcm16-aes128gcm16-ecp256,aes192-sha256-modp3072}
eval    export IPSEC_${1}IKECIPHER=\${IPSEC_${1}IKECIPHER:-aes192gcm16-aes128gcm16-prfsha256-ecp256-ecp521,aes192-sha256-modp3072}
    return 0
}

_check_variables_single() {
    _check_variables ""
}

_check_variables_multi() {
    for i in $(seq $IPSEC_NUMCONF);
    do
        _check_default_variables "CONFIGS_${i}_"
    done
}


_check_variables() {
  # we only need two varaiables for init-containers
eval  if [ -n "\$IPSEC_${1}VTI_KEY" ]; then
eval      [ -z "\$IPSEC_${1}REMOTEIP" ] && { echo "Need to set IPSEC_${1}REMOTEIP"; exit 1; }
eval      [ -z "\$IPSEC_${1}REMOTENET" ] && { echo "Need to set IPSEC_${1}REMOTENET"; exit 1; }
  else
eval      [ -z "$\IPSEC_${1}LOCALNET" ] && { echo "Need to set IPSEC_${1}LOCALNET"; exit 1; }
eval      [ -z "$\IPSEC_${1}PSK" ] && { echo "Need to set IPSEC_${1}PSK"; exit 1; }
eval      [ -z "$\IPSEC_${1}REMOTEIP" ] && { echo "Need to set IPSEC_${1}REMOTEIP"; exit 1; }
eval      [ -z "$\IPSEC_${1}REMOTEID" ] && { echo "Need to set IPSEC_${1}REMOTEID"; exit 1; }
eval      [ -z "$\IPSEC_${1}LOCALIP" ] && { echo "Need to set IPSEC_${1}LOCALIP"; exit 1; }
eval      [ -z "$\IPSEC_${1}LOCALID" ] && { echo "Need to set IPSEC_${1}LOCALID"; exit 1; }
eval      [ -z "$\IPSEC_${1}REMOTENET" ] && { echo "Need to set IPSEC_${1}REMOTENET"; exit 1; }
eval      [ -z "$\IPSEC_${1}KEYEXCHANGE" ] && { echo "Need to set IPSEC_${1}KEYEXCHANGE"; exit 1; }
eval      [ -z "$\IPSEC_${1}ESPCIPHER" ] && { echo "Need to set IPSEC_${1}ESPCIPHER"; exit 1; }
eval      [ -z "$\IPSEC_${1}IKECIPHER" ] && { echo "Need to set IPSEC_${1}IKECIPHER"; exit 1; }
  fi
eval  if [ -n "$IPSEC_${1}VTI_IPADDR_PEER" -a -z "$IPSEC_${1}VTI_IPADDR_LOCAL" ]; then
eval      echo "IPSEC_${1}VTI_IPADDR_PEER cannot be used without IPSEC_${1}VTI_IPADDR_LOCAL."
      exit 1
  fi
  return 0
}

_print_variables_single() {
    _print_variables ""
}

_print_variables_multi() {
    for i in $(seq $IPSEC_NUMCONF);
    do
        _print_variables_multi "CONFIGS_${i}_"
    done

_print_variables() {
    echo "======= set variables ======="
    eval printf "IPSEC_LOCALNET=%s\n" \$IPSEC_${1}LOCALNET
    eval printf "IPSEC_LOCALIP=%s\n" \$IPSEC_${1}LOCALIP
    eval printf "IPSEC_LOCALID=%s\n" \$IPSEC_${1}LOCALID
    eval printf "IPSEC_REMOTEID=%s\n" \$IPSEC_${1}REMOTEID
    eval printf "IPSEC_REMOTEIP=%s\n" \$IPSEC_${1}REMOTEIP
    eval printf "IPSEC_REMOTENET=%s\n" \$IPSEC_${1}REMOTENET
    eval printf "IPSEC_PSK=%s\n" \$IPSEC_${1}PSK
    eval printf "IPSEC_KEYEXCHANGE=%s\n" \$IPSEC_${1}KEYEXCHANGE
    eval printf "IPSEC_ESPCIPHER=%s\n" \$IPSEC_${1}ESPCIPHER
    eval printf "IPSEC_IKECIPHER=%s\n" \$IPSEC_${1}IKECIPHER
    eval printf "IPSEC_VTI_KEY=%s\n" \$IPSEC_${1}VTI_KEY
    eval printf "IPSEC_VTI_STATICROUTES=%s\n" \$IPSEC_${1}VTI_STATICROUTES
    eval printf "IPSEC_VTI_IPADDR_LOCAL=%s\n" \$IPSEC_${1}VTI_IPADDR_LOCAL
    eval printf "IPSEC_VTI_IPADDR_PEER=%s\n" \$IPSEC_${1}VTI_IPADDR_PEER
    return 0
}

trap _term TERM INT

# hook to initialize environment by file
[ -r "$ENVFILE" ] && . $ENVFILE

if [ -z "$IPSEC_MULTICONF" ]; then
    _set_default_variables_multi
    _check_variables_multi

    _print_variables_multi

else

    _set_default_variables_single
    _check_variables_single

    _print_variables_single
fi
_config

if [ "$1" != "show-config" ]
then

    if [ -z "$IPSEC_MULTICONF" ]
    then
        if [ "$1" = "init" ]; then
            _initialize_multi
            exit 0
        fi
    else
        if [ "$1" = "init" ]; then
            _initialize_single
            exit 0
        fi
    fi

    if  [ "$SET_ROUTE_DEFAULT_TABLE" = "TRUE" ]
    then
        if [ -z "$IPSEC_MULTICONF" ]
        then
            echo "SETUP of default route table not supported in multi config mode"
        else
            _add_route
        fi
    fi

    _start_strongswan

    _term
else
    exit 0
fi
