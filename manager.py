from typing import Dict, Set

from fastapi import WebSocket


class ConnectionManager:
    """Tracks which users are connected. One user can have multiple tabs."""

    def __init__(self):
        self.connections: Dict[int, Set[WebSocket]] = {}

    async def connect(
        self,
        user_id: int,
        ws: WebSocket,
    ):
        await ws.accept()

        self.connections.setdefault(
            user_id,
            set(),
        ).add(ws)

        print(
            f"[WS] CONNECTED user_id={user_id} "
            f"connections={len(self.connections[user_id])}"
        )

    def disconnect(
        self,
        user_id: int,
        ws: WebSocket,
    ):
        sockets = self.connections.get(user_id)

        if not sockets:
            return

        sockets.discard(ws)

        if not sockets:
            self.connections.pop(user_id, None)

        print(
            f"[WS] DISCONNECTED user_id={user_id} "
            f"remaining={len(self.connections.get(user_id, set()))}"
        )

    def is_online(self, user_id: int) -> bool:
        return user_id in self.connections

    async def send_to_user(
        self,
        user_id: int,
        data: dict,
    ):
        sockets = list(
            self.connections.get(user_id, set())
        )

        print(
            f"[WS] SEND user_id={user_id} "
            f"sockets={len(sockets)} "
            f"type={data.get('type')}"
        )

        for ws in sockets:
            try:
                await ws.send_json(data)

            except Exception as exc:
                print(
                    f"[WS] SEND FAILED "
                    f"user_id={user_id}: {repr(exc)}"
                )

                self.disconnect(
                    user_id,
                    ws,
                )

    async def broadcast(
        self,
        data: dict,
    ):
        print(
            f"[WS] BROADCAST type={data.get('type')} "
            f"users={list(self.connections.keys())}"
        )

        for user_id in list(
            self.connections.keys()
        ):
            await self.send_to_user(
                user_id,
                data,
            )


manager = ConnectionManager()