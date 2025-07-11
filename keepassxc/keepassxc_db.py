"""
Wrapper around the KeePassXC CLI

Features:
    - Keep track of passphrase unlock and inactivity lock timeouts
    - Search entries
    - Retrieve entry details (username, password, notes, URL)
"""
from typing import List, Dict, Tuple
import subprocess
import os
from datetime import datetime, timedelta


class KeepassxcCliNotFoundError(Exception):
    """
    Unable to execute KeePassXC CLI
    """


class KeepassxcFileNotFoundError(Exception):
    """
    Database file not found on the given path
    """


class KeepassxcLockedDbError(Exception):
    """
    Attempting to access locked database
    """


class KeepassxcCliError(Exception):
    """ Contains error message returned by keepassxc-cli """

    def __init__(self, message):
        super(KeepassxcCliError, self).__init__()
        self.message = message


class KeepassxcDatabase:
    """ Wrapper around keepassxc-cli """

    def __init__(self):
        self.cli = "keepassxc-cli"
        self.cli_checked = False
        self.path = None
        self.path_checked = False
        self.key_file_path = None
        self.passphrase = None
        self.passphrase_expires_at = None
        self.inactivity_lock_timeout = 0

    def initialize(self, path: str, inactivity_lock_timeout: int, key_file_path: str = None) -> None:
        """
        Check that
        - we can call invoke the CLI
        - database file at specified path exists
        - key file exists if specified

        Don't call more than once.
        """
        self.inactivity_lock_timeout = inactivity_lock_timeout
        if not self.cli_checked:
            if self.can_execute_cli():
                self.cli_checked = True
            else:
                raise KeepassxcCliNotFoundError()

        if path != self.path:
            self.path = path
            self.path_checked = False
            self.passphrase = None

        if not self.path_checked:
            if os.path.exists(self.path):
                self.path_checked = True
            else:
                raise KeepassxcFileNotFoundError()

        # Set key file path if provided
        if key_file_path:
            expanded_key_file_path = os.path.expanduser(key_file_path)
            print(f"DEBUG: Checking key file path: {expanded_key_file_path}")
            if os.path.exists(expanded_key_file_path):
                self.key_file_path = expanded_key_file_path
                print(f"DEBUG: Key file found and set: {self.key_file_path}")
            else:
                print(f"DEBUG: Key file not found: {expanded_key_file_path}")
                raise KeepassxcFileNotFoundError(f"Key file not found: {expanded_key_file_path}")
        else:
            self.key_file_path = None
            print(f"DEBUG: No key file specified")

    def change_path(self, new_path: str) -> None:
        """
        Change the path to the database file and lock the database.
        """
        self.path = os.path.expanduser(new_path)
        self.path_checked = False
        self.passphrase = None
        self.passphrase_expires_at = None

    def change_inactivity_lock_timeout(self, secs: int) -> None:
        """
        Change the inactivity lock timeout and immediately lock the database.
        """
        self.inactivity_lock_timeout = secs
        self.passphrase = None
        self.passphrase_expires_at = None

    def is_passphrase_needed(self):
        """
        Whether the user needs to enter the passphrase to unlock the database
        """
        if self.passphrase is None:
            return True
        if self.inactivity_lock_timeout:
            if datetime.now() > self.passphrase_expires_at:
                self.passphrase = None
                return True
        return False

    def verify_and_set_passphrase(self, passphrase: str) -> bool:
        """
        Try to query the database using the given passphrase,
        save the passphrase if successful
        """
        self.passphrase = passphrase
        err, out, return_code = self.run_cli("ls", "-q", self.path)
        if return_code != 0:
            self.passphrase = None
            return False
        return True

    def search(self, query: str) -> List[str]:
        """
        Search the database for entry titles that contain the given query string
        """
        if self.is_passphrase_needed():
            raise KeepassxcLockedDbError()

        (err, out, return_code) = self.run_cli("search", "-q", self.path, query)
        if return_code != 0:
            if "No results for that" in err:
                return []
            raise KeepassxcCliError(err)
        # Entry names in keepassxc-cli start with a "/"
        # (because kdbx files have a tree structure with "folders" etc)
        # For aesthetic purposes, we are removing the leading "/" here
        # by blindly cutting off the first char
        # but will add it back any time we need to pass an entry name
        # to the CLI as an argument
        return [l[1:] for l in out.splitlines()]

    def get_entry_details(self, entry: str) -> Dict[str, str]:
        """
        Retrieve details of the given entry:
        - UserName
        - Password
        - URL
        - Notes

        :param entry: full name of the entry, without the leading '/'
        :returns: dict of entry attributes and their values
        """
        if self.is_passphrase_needed():
            raise KeepassxcLockedDbError()

        attrs = dict()
        for attr in ["UserName", "Password", "URL", "Notes"]:
            (err, out, return_code) = self.run_cli("show", "-q", "-a", attr, self.path, f"/{entry}")
            if return_code != 0:
                raise KeepassxcCliError(err)
            attrs[attr] = out.strip("\n")
        return attrs

    def can_execute_cli(self) -> bool:
        """
        Whether we are able to execute the KeePassXC without an OS error
        """
        try:
            subprocess.run(
                [self.cli], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
            )
            return True
        except OSError:
            return False

    def run_cli(self, *args) -> Tuple[str, str, int]:
        """
        Execute the KeePassXC CLI with given args, parse output and handle errors
        Returns (stderr, stdout, return_code)
        """
        cli_args = [self.cli]
        
        # Add key file parameter if available - try as command option
        if self.key_file_path:
            cli_args.extend(args[:1])  # Add the command (e.g., "ls")
            cli_args.extend(["-k", self.key_file_path])  # Add key file parameter
            cli_args.extend(args[1:])  # Add remaining arguments
        else:
            cli_args.extend(args)
        
        try:
            proc = subprocess.run(
                cli_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                input=bytes(self.passphrase, "utf-8"),
                check=False,
            )
        except OSError:
            raise KeepassxcCliNotFoundError()

        if self.inactivity_lock_timeout:
            self.passphrase_expires_at = datetime.now() + timedelta(
                seconds=self.inactivity_lock_timeout
            )

        stderr = proc.stderr.decode("utf-8")
        stdout = proc.stdout.decode("utf-8")
        
        # Debug output for troubleshooting
        print(f"DEBUG: CLI command: {' '.join(cli_args)}")
        print(f"DEBUG: Return code: {proc.returncode}")
        print(f"DEBUG: Stderr: {stderr}")
        print(f"DEBUG: Stdout: {stdout}")
        print(f"DEBUG: Key file path: {self.key_file_path}")
        
        return (stderr, stdout, proc.returncode)
