from flask import Flask, request

def matrix_server(api):
    app = Flask('server')

    @app.route("/slot/<slot_index>", methods=["POST"])
    def set_slot(slot_index):
        try:
            slot = int(slot_index)
        except TypeError:
            return f"{slot_index} provided couldn't be cast to int.", 400
        gif_data = request.get_data()
        print(gif_data, flush=True)
        try:
            res = api.set_slot(slot, gif_data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return str(e), 500
        if res:
            return "", 201
        else:
            return "", 500
        
    @app.route("/ping/<ping_id>", methods=["GET"])
    def ping(ping_id):
        try:
            ping_id_int = int(ping_id)
        except TypeError:
            return f"{ping_id} provided couldn't be cast to int.", 400
        try:
            res = api.ping(ping_id_int)
        except Exception as e:
            return str(e), 500
        return {"check_int":res}
        
    return app.run
