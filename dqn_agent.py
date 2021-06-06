from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
import random, copy
import numpy as np
import re

from utils import DEBUG_PRINT, SAVE_LOG
from dialogue_config import agent_actions

# Some of the code based off of https://jaromiru.com/2016/09/27/lets-make-a-dqn-theory/
# Note: In original paper's code the epsilon is not annealed and annealing is not implemented in this code either

class DQNAgent:
    """The DQN agent that interacts with the user."""

    def __init__(self, state_size, constants):
        """
        The constructor of DQNAgent.

        The constructor of DQNAgent which saves constants, sets up neural network graphs, etc.

        Parameters:
            state_size (int): The state representation size or length of numpy array
            constants (dict): Loaded constants in dict

        """

        self.max_memory_size = constants['agent']['max_mem_size']

        self.max_round = constants['run']['max_round_num'] # number of round (one time sentence user-agent) in episode

        # the agents memory
        self.memory = []
        self.memory_index = 0

        self.lr = constants['agent']['learning_rate']
        self.gamma = constants['agent']['gamma']
        self.batch_size = constants['agent']['batch_size']
        self.hidden_size = constants['agent']['dqn_hidden_size']
        self.vanilla = constants['agent']['vanilla']

        self.state_size = state_size
        self.possible_actions = agent_actions
        self.num_actions = len(self.possible_actions)

        self.beh_model = self._build_model()
        self.tar_model = self._build_model()

        self.save_weights_file_path = constants['agent']['save_weights_file_path']
        self.load_weights_file_path = constants['agent']['load_weights_file_path']

        self._load_weights()

        self.reset()

    def reset(self):
        """Resets ..."""

    def is_memory_full(self):
        """Returns true if the memory is full."""

        return len(self.memory) >= self.max_memory_size

    def empty_memory(self):
        """Empties the memory and resets the memory index."""

        self.memory = []
        self.memory_index = 0

    def add_experience(self, state, action, reward, next_state, done):
        """
        Adds an experience tuple made of the parameters to the memory.

        Parameters:
            state (numpy.array)
            action (int)
            reward (int)
            next_state (numpy.array)
            done (bool)
        """

        if len(self.memory) < self.max_memory_size:
            self.memory.append(None)
        self.memory[self.memory_index] = (state, action, reward, next_state, done)
        self.memory_index = (self.memory_index + 1) % self.max_memory_size

    """RL Model."""
    def _build_model(self):
        """Builds and returns model/graph of neural network."""

        model = Sequential()
        model.add(Dense(self.hidden_size, input_dim=self.state_size, activation='relu'))
        model.add(Dense(self.num_actions, activation='linear'))
        model.compile(loss='mse', optimizer=Adam(lr=self.lr))
        weights = model.layers[1].get_weights()[0]
        biases = model.layers[1].get_weights()[1]

        # print("initial weights =", weights)
        # print("initial biases =", biases)
        return model

    def _dqn_predict(self, states, target=False):
        """
        Returns a model prediction given an array of states.

        Parameters:
            states (numpy.array)
            target (bool)

        Returns:
            numpy.array
        """

        if target:
            return self.tar_model.predict(states)
        else:
            return self.beh_model.predict(states)

    def train(self):
        """
        Trains the agent by improving the behavior model given the memory tuples.

        Takes batches of memories from the memory pool and processing them. The processing takes the tuples and stacks
        them in the correct format for the neural network and calculates the Bellman equation for Q-Learning.

        """

        # Calc. num of batches to run
        num_batches = len(self.memory) // self.batch_size
        for b in range(num_batches):
            batch = random.sample(self.memory, self.batch_size)

            states = np.array([sample[0] for sample in batch])
            # DEBUG_PRINT("states = ", states)
            next_states = np.array([sample[3] for sample in batch])

            assert states.shape == (self.batch_size, self.state_size), 'States Shape: {}'.format(states.shape)
            assert next_states.shape == states.shape

            beh_state_preds = self._dqn_predict(states)  # For leveling error
            # DEBUG_PRINT("beh_state_preds = ", beh_state_preds)
            if not self.vanilla:
                beh_next_states_preds = self._dqn_predict(next_states)  # For indexing for DDQN
            tar_next_state_preds = self._dqn_predict(next_states, target=True)  # For target value for DQN (& DDQN)

            inputs = np.zeros((self.batch_size, self.state_size))
            targets = np.zeros((self.batch_size, self.num_actions))

            for i, (s, a, r, s_, d) in enumerate(batch):
                # DEBUG_PRINT("i = ", i)
                t = beh_state_preds[i]
                predict = beh_state_preds[i]
                q = beh_state_preds[i][a]
                if not self.vanilla:
                    t[a] = r + self.gamma * tar_next_state_preds[i][np.argmax(beh_next_states_preds[i])] * (not d)
                else:
                    t[a] = r + self.gamma * np.amax(tar_next_state_preds[i]) * (not d)
                SAVE_LOG("input state = ", s)
                SAVE_LOG("Output predict = ", predict)
                # SAVE_LOG("Q* = ", t[a])
                loss = t[a] - q
                SAVE_LOG("loss of action [", a, "] = ", loss)

                inputs[i] = s
                targets[i] = t

            self.beh_model.fit(inputs, targets, epochs=1, verbose=0, batch_size=self.batch_size)

    def save_weights(self):
        """Saves the weights of both models in two h5 files."""

        if not self.save_weights_file_path:
            return
        beh_save_file_path = re.sub(r'\.h5', r'_beh.h5', self.save_weights_file_path)
        self.beh_model.save_weights(beh_save_file_path)
        tar_save_file_path = re.sub(r'\.h5', r'_tar.h5', self.save_weights_file_path)
        self.tar_model.save_weights(tar_save_file_path)

    def _load_weights(self):
        """Loads the weights of both models from two h5 files."""

        if not self.load_weights_file_path:
            return
        beh_load_file_path = re.sub(r'\.h5', r'_beh.h5', self.load_weights_file_path)
        self.beh_model.load_weights(beh_load_file_path)
        tar_load_file_path = re.sub(r'\.h5', r'_tar.h5', self.load_weights_file_path)
        self.tar_model.load_weights(tar_load_file_path)


    """Warmup phase."""
    def pick_action(self, action):
        """
        Return the action of the agent by using action in defined dialog.
        Check if the agent has succeeded or lost or still going.

        Using in warmup.

        Parameters:
            action (dict): The agent action that is picked in defined dialog.

        Returns:
            int: The index of the action in the possible actions
            dict: Agent response
        """

        agent_response = {}
        agent_response['intent'] = action['intent']
        agent_response['inform_slots'] = copy.deepcopy(action['inform_slots'])
        agent_response['request_slots'] = {}
        for slot in action['request_slots']:
            agent_response['request_slots'][slot] = 'UNK'

        # the format like training
        rule_response = {}
        rule_response['intent'] = agent_response['intent']
        rule_response['inform_slots'] = {}
        rule_response['request_slots'] = {}
        if not (agent_response['intent'] == 'match_found'):
            rule_response['request_slots'] = copy.deepcopy(agent_response['request_slots'])
            for slot in agent_response['inform_slots']:
                rule_response['inform_slots'][slot] = 'PLACEHOLDER'
        index = self._map_action_to_index(rule_response)
        return index, agent_response

    def _map_action_to_index(self, response):
        """
        Maps an action to an index from possible actions.

        Parameters:
            response (dict)

        Returns:
            int
        """

        for (i, action) in enumerate(self.possible_actions):
            if response == action:
                return i
        raise ValueError('Response: {} not found in possible actions'.format(response))


    """Training phase."""
    def copy(self):
        """Copies the behavior model's weights into the target model's weights."""

        self.tar_model.set_weights(self.beh_model.get_weights())

    def get_action_train(self, state):
        """
        Returns the action of the agent given a state.

        Gets the action of the agent given the current state.
        the neural networks are used to respond.

        Parameters:
            state (numpy.array): The database with format dict(long: dict)

        Returns:
            int: The index of the action in the possible actions
            dict: The action/response itself

        Inputs:
            state: current state of dialog
        """

        return self._dqn_action(state)

    def _dqn_action(self, state):
        """
        Returns a behavior model output given a state.

        Parameters:
            state (numpy.array)

        Returns:
            int: The index of the action in the possible actions
            dict: The action/response itself
        """

        prop = self._dqn_predict_one(state)
        # DEBUG_PRINT("prop action = ", prop)
        index = np.argmax(self._dqn_predict_one(state))
        action = self._map_index_to_action(index)
        return index, action

    def _map_index_to_action(self, index):
        """
        Maps an index to an action in possible actions.

        Parameters:
            index (int)

        Returns:
            dict
        """

        for (i, action) in enumerate(self.possible_actions):
            if index == i:
                return copy.deepcopy(action)
        raise ValueError('Index: {} not in range of possible actions'.format(index))

    def _dqn_predict_one(self, state, target=False):
        """
        Returns a model prediction given a state.

        Parameters:
            state (numpy.array)
            target (bool)

        Returns:
            numpy.array
        """

        return self._dqn_predict(state.reshape(1, self.state_size), target=target).flatten()
