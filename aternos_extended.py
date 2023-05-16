import os
import re
import hashlib
import logging

import base64

from typing import List, Dict, Optional

import lxml.html

from python_aternos.atserver import AternosServer
from python_aternos.atconnect import AternosConnect
from python_aternos.aterrors import CredentialsError
from python_aternos.aterrors import TwoFactorAuthError

from python_aternos import Client as AtClient


class Client(AtClient):
    @classmethod
    def from_hashed(
            cls,
            username: str,
            md5: str,
            code: Optional[int] = None,
            sessions_dir: str = '~',
            **custom_args):
        """Log in to an Aternos account with
        a username and a hashed password

        Args:
            username (str): Your username
            md5 (str): Your password hashed with MD5
            code (Optional[int]): 2FA code
            sessions_dir (str): Path to the directory
                where session will be automatically saved
            **custom_args (tuple, optional): Keyword arguments
                which will be passed to CloudScraper `__init__`

        Raises:
            CredentialsError: If the API didn't
                return a valid session cookie
        """

        filename = cls.session_file(
            username, sessions_dir
        )

        try:
            return cls.restore_session(
                filename, **custom_args
            )
        except (OSError, CredentialsError):
            pass

        atconn = AternosConnect()

        if len(custom_args) > 0:
            atconn.add_args(**custom_args)

        atconn.parse_token()
        atconn.generate_sec()

        credentials = {
            'user': username,
            'password': md5,
        }

        if code is not None:
            credentials['code'] = str(code)

        loginreq = atconn.request_cloudflare(
            'https://aternos.org/ajax/account/login',
            'POST', data=credentials, sendtoken=True
        )

        if b'"show2FA":true' in loginreq.content:
            raise TwoFactorAuthError('2FA code is required')

        if 'ATERNOS_SESSION' not in loginreq.cookies:
            raise CredentialsError(
                'Check your username and password'
            )

        obj = cls(atconn)
        obj.saved_session = filename

        try:
            obj.save_session(filename)
        except OSError:
            pass

        return obj