# Special slot values (for reference)
'UNK'  # For requests

#######################################
# Usersim Config
#######################################
# Used in EMC for intent error (and in user)
usersim_intents = ['inform', 'request', 'done']

# Required to be in the first action in inform slots of the usersim if they exist in the goal inform slots
usersim_required_init_inform_keys = ['name_product']

#######################################
# Agent Config
#######################################

# Possible inform and request slots for the agent
# agent_inform_slots = ['name_product', 'size_product', 'color_product', 'material_product', 'cost_product', 'amount_product']
agent_inform_slots = ['name_product', 'size_product', 'color_product', 'material_product', 'cost_product', 'amount_product']
agent_request_slots = ['name_product', 'size_product', 'color_product', 'material_product', 'cost_product', 'amount_product']

# Possible actions for agent
agent_actions = [
    {'intent': 'done', 'inform_slots': {}, 'request_slots': {}},  # Triggers closing of conversation
    # {'intent': 'not_found', 'inform_slots': {}, 'request_slots': {}}
]
for slot in agent_request_slots:
    agent_actions.append({'intent': 'request', 'inform_slots': {}, 'request_slots': {slot: 'UNK'}})
for slot in agent_inform_slots:
    agent_actions.append({'intent': 'inform', 'inform_slots': {slot: 'PLACEHOLDER'}, 'request_slots': {}})

#######################################
# Global config
#######################################

# These are used for both constraint check AND success check in usersim
FAIL = -1
NO_OUTCOME = 0
SUCCESS = 1
UNSUITABLE = -2

# All possible intents (for one-hot conversion in ST.get_state())
all_intents = ['done', 'inform', 'request']

# All possible slots (for one-hot conversion in ST.get_state())
all_slots = ['name_product', 'size_product', 'color_product', 'cost_product', 'material_product', 'amount_product']

# All possible slots for request product info goal
request_product_entity = {
    'all_keys': ['name_product', 'size_product', 'color_product', 'cost_product', 'material_product', 'amount_product'],
    'name_product': [],
    'material_product': ['name_product'],
    'size_product': ['name_product', 'color_product'],
    'color_product': ['name_product', 'size_product'],
    'cost_product': ['name_product'],
    'amount_product': ['name_product']
}
