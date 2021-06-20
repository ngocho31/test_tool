from inspect import getframeinfo, stack
import os

# from dialogue_config import FAIL, SUCCESS, UNSUITABLE, GOOD_INFORM, NO_VALUE
from dialogue_config import FAIL, SUCCESS

WARMUPLOG = False
TRAINLOG = False
MODELLOG = False
TESTLOG = True
DEBUG = True

def DEBUG_PRINT(*arg):
    if DEBUG:
        caller = getframeinfo(stack()[1][0])
        filename = os.path.basename(caller.filename)
        print("[%s][%s][%d]" % (filename, caller.function, caller.lineno), end =" ")
        for message in arg:
            print("%s" % (message), end ="") # python3 syntax print
        print("")

def SAVE_LOG(*arg, filename='model.log'):
    if (filename == 'warmup.log' and WARMUPLOG == False) or \
    (filename == 'train.log' and TRAINLOG == False) or \
    (filename == 'test.log' and TESTLOG == False) or \
    (filename == 'model.log' and MODELLOG == False):
        return
    string = ''
    for message in arg:
        string += str(message)
    string += '\n'
    with open(filename,'a') as f:
        f.write(string)

def reward_function(success, max_round):
    """
    Return the reward given the success.

    Return -1 + -max_round if success is FAIL, -1 + 2 * max_round if success is SUCCESS and -1 otherwise.

    Parameters:
        success (int)

    Returns:
        int: Reward
    """

    reward = -1
    if success == FAIL:
        reward += -max_round
    elif success == SUCCESS:
        reward += 2 * max_round
    # elif success == UNSUITABLE:
    #     reward += -(max_round/2)
    # elif success == GOOD_INFORM:
    #     reward += max_round
    # elif success == NO_VALUE:
    #     reward += 1
    return reward

def convert_list_to_dict(lst):
    """
    Convert list to dict where the keys are the list elements, and the values are the indices of the elements in the list.

    Parameters:
        lst (list)

    Returns:
        dict
    """

    if len(lst) > len(set(lst)):
        raise ValueError('List must be unique!')
    return {k: v for v, k in enumerate(lst)}

def check_match_sublist_and_substring(list_children, list_parent):
    count_match=0
    for children_value in list_children:
        for parent_value in list_parent:
            if children_value == parent_value:
                count_match+=1
                break
    if count_match==len(list_children):
        return True
    return False
