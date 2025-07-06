# Use different asynchronous server then werkzeug (flask-standard, is not recommended)
# import eventlet
# eventlet.monkey_patch()

from backend import create_app
from backend.extensions import socketio
from backend.config import ProductionConfig

app = create_app(config_class=ProductionConfig)

if __name__ == '__main__':
    # Change allow_unsafe_werkzeug if eventlet is imported and patches the threats in python
    socketio.run(app, allow_unsafe_werkzeug=True, host='0.0.0.0', port=5000)
