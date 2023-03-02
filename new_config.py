#
#

"""A client.yaml reconverter.

We want to go from client.yaml to sui-base.yaml
"""

import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Union
import yaml


@dataclass
class CfgPresent:
    devnet: bool = False
    localnet: bool = False
    testnet: bool = False
    mainnet: bool = False

    @classmethod
    def from_cfg(cls, in_cfg: dict) -> "CfgPresent":
        """Detect what envs found in in_cfg."""
        instance = cls()
        for cenv in in_cfg['envs']:
            match cenv['alias']:
                case 'devnet':
                    instance.devnet = True
                case 'localnet':
                    instance.localnet = True
                case 'testnet':
                    instance.testnet = True
                case 'mainnet':
                    instance.mainnet = True
                case _:
                    raise ValueError(
                        f"Don't know how to handle {in_cfg['alias']}")
        return instance


@dataclass
class KeyStore:
    File: str = ""


@dataclass
class Environment:
    active_address: str = ""
    keystore: KeyStore = field(default_factory=KeyStore(""))
    alias: str = ""
    rpc: str = ""
    ws: str = ""
    sui_version: str = ""


# Well defined environments

env_devnet = Environment("", KeyStore(""), "devnet",
                         "https://fullnode.devnet.sui.io:443", "wss://fullnode.devnet.sui.io:443")

env_localnet = Environment("", KeyStore(""), "localnet",
                           "http://0.0.0.0:9000", "ws://127.0.0.1:9000")

env_testnet = Environment("", KeyStore(""), "testnet",
                          "https://fullnode.testnet.sui.io:443", "wss://fullnode.testnet.sui.io:443")

env_mainnet = Environment("", KeyStore(""), "mainnet",
                          "http://0.0.0.0:9000", "ws://127.0.0.1:9000")


def env_for_env(target_env: str) -> Environment:
    """Fetch a predefined partial configuration."""
    oenv = None
    match target_env:
        case "devnet":
            oenv = env_devnet
        case "localnet":
            oenv = env_localnet
        case "testnet":
            oenv = env_testnet
        case "mainnet":
            oenv = env_mainnet
    return oenv


@dataclass
class SuiBaseCfg:
    active_env: str = ""
    envs: list[Environment] = field(default_factory=list[Environment])

    def environment_for(self, env_key: str) -> Environment:
        """Returns the environment data block associated with env_key

        Args:
            env_key (str): The environment name key (i.e. 'devnet', 'localnet', etc.)

        Returns:
            Environment: The resolved environment or None if no key match
        """
        envs = [hit for hit in self.envs if hit.alias == env_key]
        if envs:
            return envs[0]
        else:
            return None

    def write_to_yaml(self, in_sb_cfg: str) -> Union[IOError, None]:
        """Write configuration to yaml file

        Args:
            in_sb_cfg (str): fully qualified file location to write to

        Returns:
            Union[IOError, None]: None if no error, exception otherwise
        """
        with open(in_sb_cfg, "w", encoding="utf8") as core_file:
            core_file.write(yaml.dump(asdict(self), indent=2))

    @classmethod
    def load_sui_base_cfg(cls, in_sb_cfg: str) -> "SuiBaseCfg":
        """Construct from persist dict."""
        epath = Path(os.path.expanduser(in_sb_cfg))
        in_nb_cfg = yaml.safe_load(epath.read_text())
        base_cfg = cls(in_nb_cfg['active_env'])
        for in_env in in_nb_cfg['envs']:
            current_env = Environment(
                active_address=in_env['active_address'],
                keystore=KeyStore(in_env['keystore']['File']),
                alias=in_env['alias'],
                rpc=in_env['rpc'],
                ws=in_env['ws'],
                sui_version=in_env['sui_version'])
            base_cfg.envs.append(current_env)
        return base_cfg


def get_active_env(sui_base_cfg: str) -> str:
    try:
        base_cfg = SuiBaseCfg.load_sui_base_cfg(sui_base_cfg)
        print(base_cfg.active_env)
    except IOError:
        print("")


def set_active_env(sui_base_cfg: str, env_to_set: str) -> int:
    """Sets the active environment to env_to_set in sui_base_cfg

    Args:
        sui_base_cfg (str): Fully qualified path to sui_base config file
        env_to_set (str): Name of environment to set as active

    Returns:
        int: 0 if success, -1 otherwise
    """
    try:
        base_cfg = SuiBaseCfg.load_sui_base_cfg(sui_base_cfg)
        target_env = base_cfg.environment_for(env_to_set)
        if target_env:
            base_cfg.active_env = env_to_set
            base_cfg.write_to_yaml(sui_base_cfg)
            return 0
        raise ValueError
    except (IOError, ValueError) as ioerr:
        return -1


def set_env_value(sui_base_cfg: str, env_key: str, value_key: str, value_value: str) -> int:
    """Update a value in a configuration environment block.

    Args:
        sui_base_cfg (str): Fully qualified path to sui_base config file
        env_key (str): Name of environment to update value in
        value_key (str): The value key to update the value of
        value_value (str): The value to update

    Returns:
        int: 0 if success, -1 otherwise
    """
    print(
        f"Setting {value_key} to {value_value} for {env_key} in {sui_base_cfg}")

    # Read in the configuration
    try:
        base_cfg = SuiBaseCfg.load_sui_base_cfg(sui_base_cfg)
        target_env = base_cfg.environment_for(env_key)
        if target_env:
            if hasattr(target_env, value_key):
                setattr(target_env, value_key, value_value)
                base_cfg.write_to_yaml(sui_base_cfg)
                return 0
        raise ValueError
    except (IOError, ValueError) as ioerr:
        return -1


def _refactor_to_sui_base_cfg(in_cfg: dict) -> SuiBaseCfg:
    """Refactor inbound standard sui client.yaml to sui-base ready cfg."""
    new_cfg = SuiBaseCfg()
    print("refactoring from standard client.yaml")
    # Do initial scan for environments
    env_presents = CfgPresent.from_cfg(in_cfg)
    # We want this outside scope of environments
    new_cfg.active_env = in_cfg['active_env']

    # Start with copy of existing client.yaml envs
    for inenv in in_cfg['envs']:
        current_env = env_for_env(new_cfg.active_env)
        if new_cfg.active_env == inenv['alias']:
            current_env.active_address = in_cfg['active_address']
            current_env.keystore = KeyStore(in_cfg['keystore']['File'])
            new_cfg.envs.append(current_env)
        else:
            new_cfg.envs.append(current_env)
    # Fill in environment holes
    for key, value in asdict(env_presents).items():
        if not value:
            new_cfg.envs.append(env_for_env(key))

    return new_cfg


def create_sui_base_cfg_from(bootstrap_file: str, outbound_path: str):
    """Entry point for refactoring initial client.yaml."""
    epath = Path(os.path.expanduser(bootstrap_file))
    if epath.exists():
        cfg = _refactor_to_sui_base_cfg(yaml.safe_load(epath.read_text()))
        print(f"Writing to {outbound_path}")
        cfg.write_to_yaml(outbound_path)
        print("Success")

    else:
        print(f"File Error: {bootstrap_file} does not exist")


# if __name__ == "__main__":
#     # create_sui_base_cfg_from("~/.sui/sui_config/client.yaml", "sui-base.yaml")
#     res = set_env_value("sui-base.yaml", "mainnet", "ws", "just kidding")
#     # cfg = SuiBaseCfg.load_sui_base_cfg("sui-base.yaml")
#     set_active_env("sui-base.yaml", "mainnet")
#     set_active_env("sui-base.yaml", "devnet")
#     print(res)
