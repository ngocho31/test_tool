import eel
import json
import requests

from utils import DEBUG_PRINT, SAVE_LOG
from dialogue_config import all_intents, all_slots
from dqn_agent import DQNAgent
from state_tracker import StateTracker
from convert_to_NL import ConvertTool

def episode_reset():
    """
    Resets the episode/conversation.

    Called when init and end conversation to reset the state tracker, and agent.

    """

    DEBUG_PRINT("reset")
    done = False
    # First reset the state tracker
    state_tracker.reset()

    # # Then pick an init user action
    # user_action = user.reset()
    # print("user: {}".format(str(user_action)))
    # # And update state tracker
    # state_tracker.update_state_user(user_action)

    # Finally, reset agent
    dqn_agent.reset()

def post_user_response(user_action):
    # TODO: check done intent to end conversation

    # Update state tracker with user action
    state_tracker.update_state_user(user_action)
    DEBUG_PRINT(user_action)

    user_nl = convert_tool.convert_to_nl(user_action)
    user_nl = 'User: ' + user_nl
    eel.update_dialog(user_nl)

    done = False
    # Grab "next state" as state
    state = state_tracker.get_state(done)

    # Agent takes action given state tracker's representation of dialogue
    agent_action_index, agent_action = dqn_agent.get_action_train(state)
    # Update state tracker with the agent's action
    state_tracker.update_state_agent_test(agent_action)
    DEBUG_PRINT(agent_action)

    agent_nl = convert_tool.convert_to_nl(agent_action)
    agent_nl = 'Agent: ' + agent_nl
    eel.update_dialog(agent_nl)

def close_callback(route, websockets):
    if not websockets:
        print('Bye!')
        exit()

@eel.expose
def new_inform_slot():
    eel.new_inform_slot(all_slots)

@eel.expose
def new_request_slot():
    eel.new_request_slot(all_slots)

@eel.expose
def send():
    user_action = eel.send()()
    if type(user_action) == str:
        msg["message"] = user_action
        # msg["message"] = 'Set xanh size S con khong'
        # proxies = {'https': 'http://127.0.0.1:8888'}
        x = requests.post(url, json=msg)
        print(x.json())
        user_action = pre_processing_action(x.json())

    post_user_response(user_action)

@eel.expose
def clear_all_slots():
    eel.clear_all_slots()

@eel.expose
def end_conversation():
    eel.clear_dialog()
    eel.clear_all_slots()
    episode_reset()

@eel.expose
def show_dialog():
    eel.show_dialog()


if __name__ == "__main__":
    # Load constants json into dict
    CONSTANTS_FILE_PATH = 'constants.json'
    with open(CONSTANTS_FILE_PATH) as f:
        constants = json.load(f, encoding='utf-8')

    # Load file path constants
    file_path_dict = constants['db_file_paths']
    DATABASE_FILE_PATH = file_path_dict['database']

    # Method to model regconize user intent
    url = 'http://103.113.83.31:400/get_entity_intent'
    msg = {'message': 'somevalue'}

    # Load product DB
    database = json.load(open(DATABASE_FILE_PATH, encoding='utf-8'))

    state_tracker = StateTracker(database, constants)
    dqn_agent = DQNAgent(state_tracker.get_state_size(), constants)
    convert_tool = ConvertTool()

    eel.init('web')
    eel.get_dialog_config(all_intents)
    episode_reset()

    eel.start('index.html', mode='chrome',
                            host='localhost',
                            port=8080,
                            block=True,
                            size=(700, 480),
                            position=(0,0),
                            disable_cache=True,
                            close_callback=close_callback,
                            cmdline_args=['--browser-startup-dialog',
                                    '--incognito', '--no-experiments'])
