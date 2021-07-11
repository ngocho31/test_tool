import copy
import time
import numpy as np
import random

from utils import DEBUG_PRINT, SAVE_LOG
from utils import convert_list_to_dict
from db_query import DBQuery
from dialogue_config import all_intents, all_slots, usersim_default_key
from dialogue_config import request_product_entity
from dialogue_config import usersim_intents

class StateTracker:
    """Tracks the state of the episode/conversation and prepares the state representation for the agent."""

    def __init__(self, database, size_database, constants):
        """
        The constructor of StateTracker.

        The constructor of StateTracker which creates a DB query object, creates necessary state rep. dicts, etc. and
        calls reset.

        Parameters:
            database (dict): The database with format dict(long: dict)
            constants (dict): Loaded constants in dict

        """

        self.db_helper = DBQuery(database, size_database)
        self.match_key = usersim_default_key
        self.intents_dict = convert_list_to_dict(all_intents)
        self.num_intents = len(all_intents)
        self.slots_dict = convert_list_to_dict(all_slots)
        self.num_slots = len(all_slots)
        self.max_round_num = constants['run']['max_round_num']
        self.none_state = np.zeros(self.get_state_size())
        self.reset()
        self.done = False

    def reset(self):
        """Resets current_informs, history and round_num."""

        self.current_informs = {}
        # self.current_requests = []
        # A list of the dialogues (dicts) by the agent and user so far in the conversation
        self.history = []
        self.round_num = 0
        self.done = False

    def get_state_size(self):
        """Returns the state size of the state representation used by the agent."""

        state_size = 2 * self.num_intents + 7 * self.num_slots + self.max_round_num + 3
        # DEBUG_PRINT("state_size = ", state_size)
        return state_size

    def get_state(self, done=False):
        """
        Returns the state representation as a numpy array which is fed into the agent's neural network.

        The state representation contains useful information for the agent about the current state of the conversation.
        Processes by the agent to be fed into the neural network. Ripe for experimentation and optimization.

        Parameters:
            done (bool): Indicates whether this is the last dialogue in the episode/conversation. Default: False

        Returns:
            numpy.array: A numpy array of shape (state size,)

        """

        # If done then fill state with zeros
        if done:
            return self.none_state

        # DEBUG_PRINT("len history = ", len(self.history))
        # Get last user action
        user_action = self.history[-1]
        DEBUG_PRINT(user_action)
        # Check with all slots are informed by user, finding a product in database is exist
        db_results_dict = self.db_helper.get_db_results_for_slots(self.current_informs)
        DEBUG_PRINT("db_results_dict = ", db_results_dict)

        last_agent_action = self.history[-2] if len(self.history) > 1 else None
        DEBUG_PRINT(last_agent_action)

        # Create one-hot of intents to represent the current user action
        user_act_rep = np.zeros((self.num_intents,))
        user_act_rep[self.intents_dict[user_action['intent']]] = 1.0

        # Create bag of inform slots representation to represent the current user action
        user_inform_slots_rep = np.zeros((self.num_slots,))
        for key in user_action['inform_slots'].keys():
            user_inform_slots_rep[self.slots_dict[key]] = 1.0

        # Create bag of request slots representation to represent the current user action
        user_request_slots_rep = np.zeros((self.num_slots,))
        for key in user_action['request_slots'].keys():
            user_request_slots_rep[self.slots_dict[key]] = 1.0

        # Create bag of filled_in slots based on the current_informs
        current_informs_slots_rep = np.zeros((self.num_slots,))
        for key in self.current_informs:
            current_informs_slots_rep[self.slots_dict[key]] = 1.0

        # Create one-hot of intents to represent the last agent action
        agent_act_rep = np.zeros((self.num_intents,))
        if last_agent_action:
            agent_act_rep[self.intents_dict[last_agent_action['intent']]] = 1.0

        # Create bag of inform slots representation to represent the last agent action
        agent_inform_slots_rep = np.zeros((self.num_slots,))
        if last_agent_action:
            for key in last_agent_action['inform_slots'].keys():
                agent_inform_slots_rep[self.slots_dict[key]] = 1.0

        # Create bag of request slots representation to represent the last agent action
        agent_request_slots_rep = np.zeros((self.num_slots,))
        if last_agent_action:
            for key in last_agent_action['request_slots'].keys():
                agent_request_slots_rep[self.slots_dict[key]] = 1.0

        # Value representation of the round num
        turn_rep = np.zeros((1,)) + self.round_num / 5.

        # One-hot representation of the round num
        turn_onehot_rep = np.zeros((self.max_round_num,))
        turn_onehot_rep[self.round_num - 1] = 1.0

        # Representation of DB query results (scaled counts)
        kb_count_rep = np.zeros((self.num_slots + 1,)) + db_results_dict['matching_all_constraints'] / 100.
        for key in db_results_dict.keys():
            if key in self.slots_dict:
                kb_count_rep[self.slots_dict[key]] = db_results_dict[key] / 100.
        DEBUG_PRINT(kb_count_rep)

        # Representation of DB query results (binary)
        kb_binary_rep = np.zeros((self.num_slots + 1,)) + np.sum(db_results_dict['matching_all_constraints'] > 0.)
        for key in db_results_dict.keys():
            if key in self.slots_dict:
                kb_binary_rep[self.slots_dict[key]] = np.sum(db_results_dict[key] > 0.)
        # DEBUG_PRINT(kb_binary_rep)

        state_representation = np.hstack(
            [user_act_rep, user_inform_slots_rep, user_request_slots_rep,
            agent_act_rep, agent_inform_slots_rep, agent_request_slots_rep,
            current_informs_slots_rep,
            turn_rep, turn_onehot_rep,
            kb_binary_rep, kb_count_rep
            ]).flatten()
        # DEBUG_PRINT("-----state-----")
        DEBUG_PRINT(state_representation)
        return state_representation

    def update_state_user(self, done, user_action):
        """
        Updates the dialogue history with the user's action and augments the user's action.

        Takes a user action and updates the history. Also augments the user_action param with necessary information.

        Parameters:
            user_action (dict): The user action of format dict('intent': string, 'inform_slots': dict,
                                 'request_slots': dict) and changed to dict('intent': '', 'inform_slots': {},
                                 'request_slots': {}, 'round': int, 'speaker': 'User')
        """

        # Keep track all key are informed by user.
        # Replace the value if user informed it again.
        for key, value in user_action['inform_slots'].items():
            self.current_informs[key] = value

        user_action.update({'round': self.round_num, 'speaker': 'User'})

        if user_action['intent'] in usersim_intents:
            self.history.append(user_action)
            self.round_num += 1

        if done == True and self.done == False:
            self.done = True
        elif done == False and self.done == True:
            self.done = False
            done = True
        return done


    """Warmup phase."""
    def update_state_agent_warmup(self, agent_action, use_rule=False):
        """
        Updates the dialogue history with the agent's action and augments the agent's action.

        Takes an agent action and updates the history. Also augments the agent_action param with query information and
        any other necessary information.

        Parameters:
            agent_action (dict): The agent action of format dict('intent': string, 'inform_slots': dict,
                                 'request_slots': dict) and changed to dict('intent': '', 'inform_slots': {},
                                 'request_slots': {}, 'round': int, 'speaker': 'Agent')

        """

        if use_rule:
            self.update_state_agent_train(agent_action)
        else:
            # delete request keys when agent informed
            for slot in agent_action['inform_slots']:
                if self.current_requests.__contains__(slot):
                    self.current_requests.remove(slot)
            agent_action.update({'round': self.round_num, 'speaker': 'Agent'})
            self.history.append(agent_action)


    """Training phase."""
    def update_state_agent_train(self, agent_action):
        """
        Updates the dialogue history with the agent's action and augments the agent's action.

        Takes an agent action and updates the history. Also augments the agent_action param with query information and
        any other necessary information.

        Parameters:
            agent_action (dict): The agent action of format dict('intent': string, 'inform_slots': dict,
                                 'request_slots': dict) and changed to dict('intent': '', 'inform_slots': {},
                                 'request_slots': {}, 'round': int, 'speaker': 'Agent')

        """

        # DEBUG_PRINT(agent_action)
        if agent_action['intent'] == 'inform':
            assert agent_action['inform_slots']
            # Check with all slots are informed by user, finding a product in database is exist
            inform_slots = self.db_helper.fill_inform_slot(agent_action['inform_slots'], self.current_informs, request_product_entity)
            agent_action['inform_slots'] = inform_slots
            assert agent_action['inform_slots']
            key, value = list(agent_action['inform_slots'].items())[0]  # Only one
            assert key != 'match_found'
            assert value != 'PLACEHOLDER', 'KEY: {}'.format(key)

            if type(value) != list and value != 'no match available':
                self.current_informs[key] = value
        # If intent is match_found then fill the action informs with the matched informs (if there is a match)
        elif agent_action['intent'] == 'match_found':
            assert not agent_action['inform_slots'], 'Cannot inform and have intent of match found!'
            db_results = self.db_helper.get_db_results(self.current_informs)
            if db_results:
                # Arbitrarily pick the first value of the dict
                dict_items = random.choice(db_results)
                agent_action['inform_slots'] = copy.deepcopy(dict_items)
                agent_action['inform_slots'][self.match_key] = str(agent_action['inform_slots'])
            else:
                agent_action['inform_slots'][self.match_key] = 'no match available'
            self.current_informs[self.match_key] = agent_action['inform_slots'][self.match_key]
        # DEBUG_PRINT("agent:\t", agent_action)
        agent_action.update({'round': self.round_num, 'speaker': 'Agent'})
        self.history.append(agent_action)


    """Testing phase."""
    def update_state_agent_test(self, agent_action):
        """
        Updates the dialogue history with the agent's action and augments the agent's action.

        Takes an agent action and updates the history. Also augments the agent_action param with query information and
        any other necessary information.

        Parameters:
            agent_action (dict): The agent action of format dict('intent': string, 'inform_slots': dict,
                                 'request_slots': dict) and changed to dict('intent': '', 'inform_slots': {},
                                 'request_slots': {}, 'round': int, 'speaker': 'Agent')
        """

        self.update_state_agent_train(agent_action)
