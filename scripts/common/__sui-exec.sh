#!/bin/bash

# Call the proper sui binary and config file combination.

# You must source __globals.sh before __sui-exec.sh

sui_exec() {

  # Display some sui-base related info if called without any parameters.
  DISPLAY_SUI_BASE_HELP=false
  if [ $# -eq 0 ]; then
    DISPLAY_SUI_BASE_HELP=true
  fi

  # Quick sanity check that sui-base was properly installed.
  check_workdir_ok;

  # Identify the binary to execute
  case $WORKDIR in
  cargobin)
    # Special case for cargobin workdir
    SUI_BIN="$HOME/.cargo/bin/sui"
    ;;
  *)
    # All other workdir use the proper repo binary.
    SUI_BIN="$SUI_BIN_DIR/sui"
    ;;
  esac

  # Use the proper config automatically.
  SUI_SUBCOMMAND=$1

  LAST_ARG="${@: -1}"
  if [[ "$LAST_ARG" == "--help" || "$LAST_ARG" == "-h" ]]; then
    DISPLAY_SUI_BASE_HELP=true
  fi

  if [[ $SUI_SUBCOMMAND == "client" || $SUI_SUBCOMMAND == "console" ]]; then
    shift 1
    $SUI_BIN $SUI_SUBCOMMAND --client.config "$CLIENT_CONFIG" "$@"

    # Print a friendly warning if localnet sui process found not running.
    # Might help explain weird error messages...
    if [ "$DISPLAY_SUI_BASE_HELP" = false ]; then
      update_SUI_PROCESS_PID_var;
      if [ -z "$SUI_PROCESS_PID" ]; then
        echo
        echo "Warning: localnet not running"
        echo "Do 'localnet start' to get it started."
      fi
    fi
    exit
  fi

  if [[ $SUI_SUBCOMMAND == "network" ]]; then
    shift 1
    $SUI_BIN $SUI_SUBCOMMAND --network.config "$NETWORK_CONFIG" "$@"
    exit
  fi

  if [[ $SUI_SUBCOMMAND == "genesis" ]]; then
    # Protect the user from damaging its localnet
    if [[ "$2" == "--help" || "$2" == "-h" ]]; then
      $SUI_BIN genesis --help
    fi
    echo
    setup_error "Use sui-base 'localnet start' script instead"
  fi

  if [[ $SUI_SUBCOMMAND == "start" ]]; then
    # Protect the user from starting more than one sui process.
    if [[ "$2" == "--help" || "$2" == "-h" ]]; then
      $SUI_BIN start --help
    fi
    echo
    setup_error "Use sui-base 'localnet start' script instead"
  fi

  # Are you getting an error : The argument '--keystore-path <KEYSTORE_PATH>' was provided
  # more than once, but cannot be used multiple times?
  #
  # This is because by default lsui point to the keystore created with the localnet.
  #
  # TODO Fix this. Still default to workdirs, but allow user to override with its own --keystore-path.
  #
  if [[ $SUI_SUBCOMMAND == "keytool" ]]; then
    shift 1
    $SUI_BIN $SUI_SUBCOMMAND --keystore-path "$CONFIG_DATA_DIR/sui.keystore" "$@"
    exit
  fi

  # By default, just pass transparently everything to the proper sui binary.
  $SUI_BIN "$@"

  if [ "$DISPLAY_SUI_BASE_HELP" = true ]; then
    update_ACTIVE_WORKDIR_var;
    if [ -n "$ACTIVE_WORKDIR" ]; then
      echo
      echo "$ACTIVE_WORKDIR is set-active for asui"
    fi
  fi
}
export -f sui_exec
