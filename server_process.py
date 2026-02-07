import asyncio
import json
import os
from pathlib import Path
import socket
from aiohttp import web
from player import Player
from lobby_logic import assign_team

routes = web.RouteTableDef()

@routes.get('/')
async def handle_telecommande(request):
    BASE_DIR = Path(__file__).parent
    path_html = BASE_DIR / "templates" / "telecommande.html"
    with open(path_html, encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html")

@routes.get('/ws')
async def ws_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    connected_players = request.app["connected_players"]
    game_started = request.app["game_started"]
    pseudo = None

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    pseudo = data.get("pseudo", "Guest")
                    cmd = data.get("command")

                    # Init le joueur si pas existant
                    if pseudo not in connected_players:
                        new_id = len(connected_players) + 1
                        # Choix de l'équipe
                        team = assign_team(connected_players)
                        p = Player(pseudo=pseudo, team=team)
                        connected_players[pseudo] = {
                            "id":     new_id,
                            "player": p.to_dict(),
                            "inputs": {
                                "dx": 0.0, "dy": 0.0,
                                "aim_dx":0.0, "aim_dy":0.0,
                                "shoot_angle": None
                            }
                        }
                        pid = connected_players[pseudo]["id"]
                        # On informe le client
                        await ws.send_json({"type": "assign_id", "player_id": pid})

                    entry = connected_players[pseudo]
                    p_data = entry["player"]
                    inputs = entry["inputs"]

                    if cmd == "MOVE_VECTOR":
                        inputs["dx"] = float(data.get("dx", 0))
                        inputs["dy"] = float(data.get("dy", 0))

                    elif cmd == "AIM_VECTOR":
                        inputs["aim_dx"] = float(data.get("dx", 0))
                        inputs["aim_dy"] = float(data.get("dy", 0))

                    elif cmd == "SHOOT_ANGLE":
                        angle = float(data.get("angle", 0))
                        inputs["shoot_angle"] = angle

                    # Retrieve existing entry so we keep "id"
                    entry = connected_players[pseudo]
                    entry["player"] = p_data
                    entry["inputs"] = inputs
                    connected_players[pseudo] = entry


                except json.JSONDecodeError:
                    print("[Server] Erreur JSON:", msg.data)

            elif msg.type == web.WSMsgType.ERROR:
                print("[Server] WebSocket fermé avec erreur:", ws.exception())

    finally:
        return ws

@routes.get('/status')
async def handle_status(request):
    game_started = request.app["game_started"]
    return web.json_response({"game_started": game_started.value})

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

async def init_app(connected_players, game_started):
    app = web.Application()
    app["connected_players"] = connected_players
    app["game_started"] = game_started
    app.add_routes(routes)
    STATIC_DIR = Path(__file__).parent / "static" 
    app.router.add_static('/static/', path=STATIC_DIR, name='static')
    
    return app

async def run_webapp(connected_players, game_started):
    app = await init_app(connected_players, game_started)
    runner = web.AppRunner(app)
    await runner.setup()
    server_ip = get_local_ip()
    site = web.TCPSite(runner, server_ip, 8081)
    await site.start()
    print(f"[WebApp] Démarré sur http://{server_ip}:8081")
    while True:
        try:
            await asyncio.sleep(3600)
        except asyncio.CancelledError:
            print("[WebApp] Fermeture propre.")


def webapp_main(connected_players, game_started):
    asyncio.run(run_webapp(connected_players, game_started))
