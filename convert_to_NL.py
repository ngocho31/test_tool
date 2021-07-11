import json
import random
import copy

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

class ConvertTool:
    """Convert user action to natural language."""

    def __init__(self):
        # Load constants json into dict
        NL_FILE_PATH = 'data/product_nl.json'
        with open(NL_FILE_PATH) as f:
            self.nl_db = json.load(f, encoding='utf-8')

    # convert semantic frame to natural language
    def NLG(self, action_send, NL_db):
        action = copy.deepcopy(action_send)
        sentence_list = []
        val_islist = False
        if action['speaker'] == 'User':
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
                                    m = int(int(action['inform_slots'][slot]) / 100)
                                    cm = int(action['inform_slots'][slot]) - 100
                                    val_str = str(m) + 'm' + str(cm)
                                elif isinstance(action['inform_slots'][slot], list):
                                    val_islist = True
                                    val_str = ''
                                    for i, val in enumerate(action['inform_slots'][slot]):
                                        if i == len(action['inform_slots'][slot])-1 and i > 0:
                                            val_str += ' và ' + str(val)
                                        else:
                                            val_str += str(val) + ', '
                                else:
                                    if action['inform_slots'][slot] == 'anything':
                                        action['inform_slots'][slot] = 'gì cũng được'
                                    val_str = str(action['inform_slots'][slot])
                                pos1 = pos[0]-1 if pos[0] != 0 else pos[0]
                                rep_dict.update({s[pos1:(pos[1])]: ' ' + val_str + ' '})
                    for i, j in rep_dict.items():
                        s = s.replace(i, j)
                    # DEBUG_PRINT(s)
                    return s

        if action['speaker'] == 'Agent':
            # agent action have inform/request slots
            if agent_intent_list.__contains__(action['intent']):
                # find a sentence in NL list have the same slots with agent action
                if 'no match available' in list(action['inform_slots'].values()):
                    action['intent'] = 'not_found'
                    for key, val in action['inform_slots'].items():
                        action['request_slots'].update({key: 'UNK'})
                    action['inform_slots'].clear()
                if action['intent'] == 'match_found':
                    if action['inform_slots']['color_product'] == 'None':
                        action['inform_slots'].pop('color_product', None)
                    action['inform_slots'].pop('material_product', None)
                    action['inform_slots'].pop('amount_product', None)
                    action['inform_slots'].pop('shopping', None)
                elif ('size_product' in list(action['inform_slots'].keys())) and (isinstance(action['inform_slots']['size_product'], str)):
                    action['inform_slots'].update({'size_customer': action['inform_slots']['size_product']})
                    action['inform_slots'].pop('size_product', None)
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
                                        val_islist = True
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
                    if val_islist:
                        if list(action['inform_slots'].keys())[0] == 'size_product':
                            s = s + ". Bạn cho mình xin đủ chiều cao, cân nặng, số đo vòng eo để shop tư vấn cho mình size phù hợp nhất nhé?"
                        elif list(action['inform_slots'].keys())[0] == 'color_product':
                            s = s + ". Bạn lấy màu gì ạ?"
                        elif list(action['inform_slots'].keys())[0] == 'cost_product':
                            s = s + ". Bạn muốn tầm giá nào ạ?"
                    elif 'color_product' in list(action['inform_slots'].keys()) and action['inform_slots']['color_product'] == 'None':
                        s = 'Dạ, Sản phẩm chỉ có một màu vậy thôi nha bạn.'
                    return s

        # DEBUG_PRINT(action)
        return action

    # convert action to NL
    def convert_to_nl(self, action):
        output = self.NLG(action, self.nl_db)
        return output

