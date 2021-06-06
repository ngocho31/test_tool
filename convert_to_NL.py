import json
import random

from utils import DEBUG_PRINT, SAVE_LOG

""" Define global variable """
user_intent_list = {
    "order": "Order",
    "changing": "Changing",
    "return": "Return",
    "inform": "Inform",
    "request": "Request",
    "hello": "Hello",
    "done": "Done",
    "connect": "Connect",
    "feedback": "feedback",
    "ok": "ok",
    "reject": "reject"
}

agent_intent_list = {
    "inform": "Shop_inform",
    "not_found": "Shop_not-found",
    "request": "Shop_request",
    "confirm": "Shop_confirm",
    "reject": "Shop_Reject",
    "hello": "Shop_Hello",
    "done": "Shop_Done",
    "not_found": "Shop_not-found",
    "match_found": "Shop_match-found",
    "connect": "Shop_connect",
    "unsuitable": "Shop_unsuitable"
}

product_entity_list = [
    "name_product",
    "size_product",
    "color_product",
    "material_product",
    "cost_product",
    "amount_product"
]

class ConvertTool:
    """Convert user action to natural language."""

    def __init__(self):
        # Load constants json into dict
        NL_FILE_PATH = 'data/product_nl.json'
        with open(NL_FILE_PATH) as f:
            self.nl_db = json.load(f, encoding='utf-8')

    # convert semantic frame to natural language
    def NLG(self, action, NL_db):
        sentence_list = []
        if action['speaker'] == 'User':
            # # user action does not have inform/request slots
            # if user_intent_list_none_slot.__contains__(action['intent']):
            #     # pick random sentence from list
            #     return random.choice(sentences_none_slot[user_intent_list_none_slot[action['intent']]])
            # # user action have inform/request slots
            # check intent is valid
            if user_intent_list.__contains__(action['intent']):
                # find a sentence in NL list have the same slots with user action
                for sentence in NL_db[user_intent_list[action['intent']]]:
                    match = True
                    NL_list = []
                    action_list = []
                    for slot in sentence['inform_slots']:
                        NL_list.append(slot[2])
                    for slot in action['inform_slots']:
                        action_list.append(slot)
                    for slot in NL_list + action_list:
                        if (NL_list == []) or (slot not in NL_list or slot not in action_list):
                            match = False
                    request_slots_list = list(action['request_slots'].keys())
                    # DEBUG_PRINT(request_slots_list)
                    for slot in sentence['request_slots'] + request_slots_list:
                        if (sentence['request_slots'] == []) or (slot not in sentence['request_slots'] or slot not in request_slots_list):
                            match = False
                    # if the same, add sentence into list
                    if match:
                        sentence_list.append(sentence)
                # pick random sentence from list
                if sentence_list:
                    sentence = random.choice(sentence_list)
                    # replace the value of slot in sentence
                    s = sentence['text']
                    # print(s)
                    rep_dict = {}
                    for slot in action['inform_slots']:
                        for pos in sentence['inform_slots']:
                            if slot == pos[2]:
                                # especially, in case inform weight or height of customer
                                if slot == "weight_customer":
                                    val_str = str(action['inform_slots'][slot]) + 'kg'
                                elif slot == "height_customer":
                                    m = int(action['inform_slots'][slot] / 100)
                                    cm = action['inform_slots'][slot] - 100
                                    val_str = str(m) + 'm' + str(cm)
                                elif isinstance(action['inform_slots'][slot], list):
                                    val_str = ''
                                    for i, val in enumerate(action['inform_slots'][slot]):
                                        if i == len(action['inform_slots'][slot])-1 and i > 0:
                                            val_str += ' và ' + str(val)
                                        else:
                                            val_str += str(val) + ', '
                                else:
                                    val_str = str(action['inform_slots'][slot])
                                pos1 = pos[0]-1 if pos[0] != 0 else pos[0]
                                rep_dict.update({s[pos1:(pos[1])]: ' ' + val_str + ' '})
                    for i, j in rep_dict.items():
                        s = s.replace(i, j)
                    # DEBUG_PRINT(s)
                    return s

        if action['speaker'] == 'Agent':
            # # agent action does not have inform/request slots
            # if agent_intent_list_none_slot.__contains__(action['intent']):
            #     # pick random sentence from list
            #     return random.choice(sentences_none_slot[agent_intent_list_none_slot[action['intent']]])
            # agent action have inform/request slots
            if agent_intent_list.__contains__(action['intent']):
                # find a sentence in NL list have the same slots with agent action
                # if 'no match available' in action['inform_slots'].values():
                #     action['intent'] = 'not_found'
                for sentence in NL_db[agent_intent_list[action['intent']]]:
                    match = True
                    NL_list = []
                    action_list = []
                    for slot in sentence['inform_slots']:
                        NL_list.append(slot[2])
                    if action['inform_slots']:
                        for slot in action['inform_slots']:
                            action_list.append(slot)
                    for slot in NL_list + action_list:
                        if (NL_list == []) or (slot not in NL_list or slot not in action_list):
                            match = False
                    request_slots_list = list(action['request_slots'].keys())
                    for slot in sentence['request_slots'] + request_slots_list:
                        if (slot not in sentence['request_slots']) or (slot not in request_slots_list):
                            match = False
                    # if the same, add sentence into list
                    if match:
                        sentence_list.append(sentence)
                # pick random sentence from list
                if sentence_list:
                    sentence = random.choice(sentence_list)
                    # replace the value of slot in sentence
                    s = sentence['text']
                    # print(s)
                    rep_dict = {}
                    for slot in action['inform_slots']:
                        for pos in sentence['inform_slots']:
                            if slot == pos[2]:
                                if slot == 'amount_product':
                                    if len(action['inform_slots'][slot]) > 0:
                                        val_str = 'còn'
                                    else:
                                        val_str = 'ko còn'
                                else:
                                    if isinstance(action['inform_slots'][slot], list):
                                        val_str = ''
                                        for i, val in enumerate(action['inform_slots'][slot]):
                                            if i == len(action['inform_slots'][slot])-1 and i > 0:
                                                val_str += ' và ' + str(val)
                                            elif i == 0:
                                                val_str += str(val)
                                            else:
                                                val_str += ', ' + str(val)
                                    else:
                                        val_str = str(action['inform_slots'][slot])
                                rep_dict.update({s[pos[0]:(pos[1])]: val_str})
                    for i, j in rep_dict.items():
                        s = s.replace(i, j)
                    # DEBUG_PRINT(s)
                    return s

        DEBUG_PRINT(action)
        # save the actions without the corresponding natural language
        # action_save.append(action)
        return ''

    # convert action to NL
    def convert_to_nl(self, action):
        # output.append('Start conversation!\n')
        # for action in action_list:
        #     print(action)
        #     conversation_NL.append(action['speaker'] + ': ' + NLG(action, nl_db) + '\n')
        output = self.NLG(action, self.nl_db)
        return output

