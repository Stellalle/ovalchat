"""
The backend API that runs dialog agents, returns agent utterance to the front-end

The API has the following functions that can be used by any front-end.
All inputs/outputs are string, except for `log_object` which is a json object and `turn_id` which are integers.
- `/chat`
Inputs: (experiment_id, new_user_utterance, dialog_id, turn_id, system_name)
Outputs: (agent_utterance, log_object)

`turn_id` starts from 0 and is incremented by 1 after a user and agent turn
"""

import logging

from flask import Flask, request
from flask_cors import CORS
from flask_restful import Api, reqparse
import os
import time
import tempfile

# set up the Flask app
app = Flask(__name__)
CORS(app)
api = Api(app)

logging.basicConfig(level=logging.INFO)
logger = app.logger


# The input arguments coming from the front-end
req_parser = reqparse.RequestParser()
req_parser.add_argument("experiment_id", type=str, location='json',
                        help='Identifier that differentiates data from different experiments.')
req_parser.add_argument("dialog_id", type=str, location='json',
                        help='Globally unique identifier for each dialog')
req_parser.add_argument("turn_id", type=int, location='json',
                        help='Turn number in the dialog')
req_parser.add_argument("new_user_utterance", type=str,
                        location='json', help='The new user utterance')
req_parser.add_argument("system_name", type=str, location='json',
                        help='The system to use for generating agent utterances')


def write_user_input_to_file(user_input):
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
        temp_file.write(user_input)
        temp_filename = temp_file.name
    os.rename(temp_filename, 'user_input.txt')


def wait_and_read_agent_output_from_file():
    while not os.path.exists('agent_output_completed.txt'):
        print(f"Waiting for agent to respond...")
        time.sleep(0.5)  # seconds
    with open('agent_output.txt', 'r') as f:
        agent_output = "\n".join(f.readlines())
    os.remove('agent_output.txt')
    os.remove('agent_output_completed.txt')
    return agent_output


def remove_all_conversation_files():
    if os.path.exists('user_input.txt'):
        os.remove('user_input.txt')
    if os.path.exists('agent_output.txt'):
        os.remove('agent_output.txt')
    if os.path.exists('agent_output_completed.txt'):
        os.remove('agent_output_completed.txt')


@app.route("/chat", methods=["POST"])
def chat():
    global user_input_global

    """
    Inputs: (experiment_id, new_user_utterance, dialog_id, turn_id, system_name)
    Outputs: (agent_utterance, log_object)
    """
    logger.info('Entered /chat')
    request_args = req_parser.parse_args()
    logger.info('Input arguments received: %s', str(request_args))

    experiment_id = request_args['experiment_id']
    new_user_utterance = request_args['new_user_utterance']
    dialog_id = request_args['dialog_id']
    turn_id = request_args['turn_id']
    system_name = request_args['system_name']

    logger.info('request from IP address %s', str(request.remote_addr))

    # Get a clean initial state for file-based I/O
    remove_all_conversation_files()

    write_user_input_to_file(new_user_utterance)
    agent_utterance = wait_and_read_agent_output_from_file()
    print(f"agent_utterance: {agent_utterance}")

    # return {'agent_utterance': 'Sample agent utterance. experiment_id=%s, new_user_utterance=%s, dialog_id=%s, turn_id=%d, system_name=%s' % (experiment_id, new_user_utterance, dialog_id, turn_id, system_name), 'log_object': {'log object parameter 1': 'log object value 1'}}
    # return {'agent_utterance': f"{agent_utterance}, experiment_id={experiment_id}, new_user_utterance={new_user_utterance}, dialog_id={dialog_id}, turn_id={turn_id}, system_name={system_name}"}
    return {'agent_utterance': agent_utterance}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)


# Example curl command for testing:
# curl http://127.0.0.1:5001/chat -d '{"experiment_id": "test_experiment", "dialog_id": "test_dialog", "turn_id": 0, "system_name": "retrieve_and_generate", "new_user_utterance": "who stars in the wandering earth 2?"}' -X POST -H 'Content-Type: application/json'