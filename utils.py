from inspect import getframeinfo, stack
import os

from dialogue_config import FAIL, SUCCESS, UNSUITABLE

WARMUPLOG = False
TRAINLOG = False
MODELLOG = False

def DEBUG_PRINT(*arg):
    caller = getframeinfo(stack()[1][0])
    filename = os.path.basename(caller.filename)
    print("[%s][%s]" % (filename, caller.function), end =" ")
    for message in arg:
        print("%s" % (message), end ="") # python3 syntax print
    print("")

def SAVE_LOG(*arg, filename='model.log'):
    if (filename == 'warmup.log' and WARMUPLOG == False) or \
    (filename == 'train.log' and TRAINLOG == False) or \
    (filename == 'model.log' and MODELLOG == False):
        return
    string = ''
    for message in arg:
        string += str(message)
    string += '\n'
    with open('logs/' + filename,'a') as f:
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
    elif success == UNSUITABLE:
        reward += -(max_round/2)
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
