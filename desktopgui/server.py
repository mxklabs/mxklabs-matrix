import base64 

from flask import Flask, request, jsonify

from slotmanager import SlotType

def matrix_server(api):
    app = Flask('server')

    @app.route("/slot/<slot_index>", methods=["DELETE"])
    def clear_slot(slot_index):
        try:
            slot = int(slot_index)
        except TypeError:
            return f"{slot_index} provided couldn't be cast to int.", 400
        try:
            res = api.set_slot(slot, None, None)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return str(e), 500
        if res:
            return "", 200
        else:
            return "", 500

    @app.route("/slot/<slot_index>", methods=["POST"])
    def set_slot(slot_index):
        try:
            slot = int(slot_index)
        except TypeError:
            return f"{slot_index} provided couldn't be cast to int.", 400
        req = request.get_json()
        # print(gif_data, flush=True)
        try:
            res = api.set_slot(slot_index, SlotType(req["slotType"]), base64.b64decode(req["data"]))
        except Exception as e:
            import traceback
            traceback.print_exc()
            return str(e), 500
        if res:
            return "", 201
        else:
            return "", 500

    @app.route("/slot/<slot_index>", methods=["GET"])
    def get_slot(slot_index):
        try:
            slot = int(slot_index)
            api_res = api.get_slot(slot)
            if api_res is None:
                return '', 204
            else:
                slot_type, gif_data = api_res
                return jsonify({
                  "slotType" : int(slot_type),
                  "data" : base64.b64encode(gif_data).decode('ascii')
                }), 200
        except Exception as e:
            import traceback
            traceback.print_exc()
            return str(e), 500
        

    @app.route("/live", methods=["POST"])
    def set_live():
        gif_data = request.get_data()
        #print(gif_data, flush=True)
        try:
            res = api.set_live(gif_data)
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
