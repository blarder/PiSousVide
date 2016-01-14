import asyncio
from functools import partial
from aiohttp import web
from .controller import HeaterController


async def set_target(heater_controller, request):
    try:
        target = float(request.match_info['target'])
        heater_controller.set_target(target)

    except ValueError:
        return web.Response(status=400)

    return web.Response(body=bytes('Set target: {}'.format(target), encoding='utf8'))


async def get_status(heater_controller, request):
    return web.json_response(heater_controller.get_status())


async def read_heater_state(heater_controller, delay):
    while True:
        await heater_controller.read_state()
        await asyncio.sleep(delay)


async def update_heater(heater_controller, delay):
    while True:
        await heater_controller.update_state()
        await asyncio.sleep(delay)


def run_server(ip='0.0.0.0', port=8000, debug=True):
    loop = asyncio.get_event_loop()
    heater_controller = HeaterController(debug=debug, loop=loop)

    app = web.Application()
    app.router.add_route('GET', '/status', partial(get_status, heater_controller))
    app.router.add_route('POST', '/target/{target}', partial(set_target, heater_controller))

    handler = app.make_handler()
    coro = loop.create_server(handler, host=ip, port=port)
    server = loop.run_until_complete(coro)

    read_task = loop.create_task(read_heater_state(heater_controller, 1))
    update_task = loop.create_task(update_heater(heater_controller, 10))

    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.run_until_complete(handler.finish_connections(1.0))
    server.close()
    read_task.cancel()
    update_task.cancel()
    loop.run_until_complete(server.wait_closed())
    loop.run_until_complete(app.finish())
    loop.close()
    print('Cleaned up properly')
