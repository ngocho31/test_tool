import eel
import json
import requests

from utils import DEBUG_PRINT, SAVE_LOG
from dialogue_config import usersim_intents, usersim_inform_slots
from dialogue_config import intent_list, entity_list
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
    done = False
    if type(user_action) == str:
        msg["message"] = user_action
        # msg["message"] = 'Set xanh size S con khong'
        # proxies = {'https': 'http://127.0.0.1:8888'}
        DEBUG_PRINT("send mess: ", user_action)
        x = requests.post(url, json=msg)
        DEBUG_PRINT("user action: ", x.json())

        # Update dialog
        user_nl = 'User: ' + user_action
        eel.update_dialog(user_nl)

        # Convert user NL to user action
        user_action = pre_processing_action(x.json())

        if user_action['intent'] == 'order':
            user_action['intent'] = 'inform'
        if user_action['intent'] in usersim_intents:
            # Update state tracker with user action
            state_tracker.update_state_user(user_action)
    else:
        # Update state tracker with user action
        state_tracker.update_state_user(user_action)
        DEBUG_PRINT("user action: ", user_action)

        # Convert user action to user NL
        user_nl = convert_tool.convert_to_nl(user_action)

        # Update dialog
        user_nl = 'User: ' + user_nl
        eel.update_dialog(user_nl)
    SAVE_LOG(user_action, filename='dialog.log')

    # TODO: check done intent to end conversation

    # Check user intent in based-rule policy:
    if user_action['intent'] in usersim_intents:
        # Grab "next state" as state
        state = state_tracker.get_state(done)

        # Agent takes action given state tracker's representation of dialogue
        agent_action_index, agent_action = dqn_agent.get_action_train(state)
    elif user_action['intent'] == 'hello':
        agent_action = {}
        agent_action['intent'] = 'hello'
        agent_action['inform_slots'] = {}
        agent_action['request_slots'] = {}
    else:
        agent_action = {}
        agent_action['intent'] = 'reject'
        agent_action['inform_slots'] = {}
        agent_action['request_slots'] = {}

    # Update state tracker with the agent's action
    state_tracker.update_state_agent_test(agent_action)
    DEBUG_PRINT("agent action: ", agent_action)
    SAVE_LOG(agent_action, filename='dialog.log')

    agent_nl = convert_tool.convert_to_nl(agent_action)
    agent_nl = 'Agent: ' + agent_nl
    eel.update_dialog(agent_nl)

def pre_processing_action(dict):
    user_action = {}
    user_action["inform_slots"] = {}
    user_action["request_slots"] = {}
    user_action["intent"] = intent_list[dict["intent"]]
    for slot in dict["entity"]:
        user_action["inform_slots"][entity_list[slot[0]]] = slot[1]
    if type(dict["request_slots"]) == list:
        for slot in dict["request_slots"]:
            user_action["request_slots"][entity_list[slot[0]]] = 'UNK'
    elif dict["request_slots"]:
        user_action["request_slots"][entity_list[dict["request_slots"]]] = 'UNK'
    return user_action

def close_callback(route, websockets):
    if not websockets:
        print('Bye!')
        exit()

@eel.expose
def new_inform_slot():
    eel.new_inform_slot(usersim_inform_slots)

@eel.expose
def new_request_slot():
    eel.new_request_slot(usersim_inform_slots)

@eel.expose
def send():
    user_action = eel.send()()
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

    max_round_num = constants['run']['max_round_num']

    # Method to model regconize user intent
    url = 'http://103.113.83.31:400/get_entity_intent'
    msg = {'message': 'somevalue'}

    # Load product DB
    database = json.load(open(DATABASE_FILE_PATH, encoding='utf-8'))

    state_tracker = StateTracker(database, constants)
    dqn_agent = DQNAgent(state_tracker.get_state_size(), constants)
    convert_tool = ConvertTool()

    eel.init('web')
    eel.get_dialog_config(usersim_intents)
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
