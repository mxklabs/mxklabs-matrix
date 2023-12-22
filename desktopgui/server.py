from flask import Flask, request

def matrix_server(api):
    app = Flask(__name__)

    @app.route("/slot/<slot_index>", methods=["POST"])
    def set_slot(slot_index):
        try:
            slot = int(slot_index)
        except TypeError:
            return f"{slot_index} provided couldn't be cast to int.", 400
        gif_data = request.get_data()
        try:
            res = api.set_slot(slot, gif_data)
        except Exception as e:
            return str(e), 500
        if res:
            return "", 201
        else:
            return "", 500
        
    return app.run