from __future__ import annotations

"""Tiny socket server to stream verbs into a TripDModel instance."""

from pathlib import Path
import socket
import threading
from typing import Optional

try:  # pragma: no cover - prefer package import
    from .tripd import TripDModel  # type: ignore
except ImportError:  # pragma: no cover - fallback when run directly
    from tripd import TripDModel  # type: ignore


def _handle_conn(conn: socket.socket, model: TripDModel) -> None:
    with conn, conn.makefile("r", encoding="utf-8") as fh:
        for line in fh:
            verb = line.strip()
            if verb:
                model.extra_verbs.append(verb)


def start_verb_stream(
    model: TripDModel,
    host: str = "127.0.0.1",
    port: int = 8765,
    unix_socket: Optional[str] = None,
) -> threading.Thread:
    """Start a background thread that listens for verbs.

    Parameters
    ----------
    model:
        The :class:`TripDModel` whose ``extra_verbs`` list will be extended.
    host, port:
        TCP address to bind when ``unix_socket`` is not provided.
    unix_socket:
        Path of a UNIX domain socket to use instead of TCP.

    Returns
    -------
    threading.Thread
        The daemon thread running the server.
    """

    def server_loop() -> None:
        if unix_socket:
            addr = Path(unix_socket)
            if addr.exists():
                addr.unlink()
            srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            srv.bind(unix_socket)
        else:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.bind((host, port))
        srv.listen()
        while True:
            conn, _ = srv.accept()
            threading.Thread(
                target=_handle_conn, args=(conn, model), daemon=True
            ).start()

    thread = threading.Thread(target=server_loop, daemon=True)
    thread.start()
    return thread


__all__ = ["start_verb_stream"]
