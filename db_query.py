from collections import defaultdict
import copy
import random

from utils import DEBUG_PRINT, SAVE_LOG
from utils import check_match_sublist_and_substring
from dialogue_config import no_query_keys, usersim_default_key

class DBQuery:
    """Queries the database for the state tracker."""

    def __init__(self, database):
        """
        The constructor for DBQuery.

        Parameters:
            database (dict): The database in the format dict(long: dict)
        """

        self.database = database
        # {frozenset: {string: int}} A dict of dicts
        self.cached_db_slot = defaultdict(dict)
        # {frozenset: {'#': {'slot': 'value'}}} A dict of dicts of dicts, a dict of DB sub-dicts
        self.cached_db = defaultdict(list)
        self.no_query = no_query_keys
        self.match_key = usersim_default_key

    def _check_constraints(self, current_requests, db_results, entity_list):
        request_key = current_requests[0] if type(current_requests) == list and current_requests else current_requests
        not_match = False
        if request_key:
            for entity in entity_list[request_key]:
                # get all val of entity need to check
                val_list = []
                for data in db_results:
                    if not val_list.__contains__(data[entity]):
                        val_list.append(data[entity])
                # if request_key == 'name_product':
                #     DEBUG_PRINT("val_list = ", val_list)
                # base on val of it, get val of request key
                if len(val_list) > 1:
                    val_request_key = []
                    for i, val in enumerate(val_list):
                        val_request_key.append(None)
                        val_request_key[i] = []
                        for data in db_results:
                            if val == data[entity] and not val_request_key[i].__contains__(data[request_key]):
                                val_request_key[i].append(data[request_key])
                    # if request_key == 'name_product':
                    #     DEBUG_PRINT("val_request_key[0] = ", val_request_key[0])
                    check = val_request_key[0]
                    for val in val_request_key[1:]:
                        # if request_key == 'name_product':
                        #     DEBUG_PRINT("val++ = ", val)
                        if not check_match_sublist_and_substring(val, check):
                            # if request_key == 'name_product':
                                # DEBUG_PRINT("not match")
                            not_match = True
                            return not_match
        return not_match

    def _count_slot_values(self, key, db_subdict):
        """
        Return a dict of the different values and occurrences of each, given a key, from a sub-dict of database

        Parameters:
            key (string): The key to be counted
            db_subdict (dict): A sub-dict of the database

        Returns:
            dict: The values and their occurrences given the key
        """

        slot_values = defaultdict(int)  # init to 0
        for db in db_subdict:
            current_option_dict = db
            # If there is a match
            if key in current_option_dict.keys():
                slot_value = current_option_dict[key]
                # This will add 1 to 0 if this is the first time this value has been encountered, or it will add 1
                # to whatever was already in there
                slot_values[slot_value] += 1
        return slot_values

    def get_db_results_for_slots(self, current_informs):
        """
        Counts occurrences of each current inform slot (key and value) in the database items.

        For each item in the database and each current inform slot if that slot is in the database item (matches key
        and value) then increment the count for that key by 1.

        If don't have any informed entity, return all 0

        Parameters:
            current_inform_slots (dict): The current informs/constraints

        Returns:
            dict: Each key in current_informs with the count of the number of matches for that key
        """

        # update_current_informs = copy.deepcopy(current_informs)
        # if 'amount_product' not in update_current_informs:
        #     update_current_informs.update({'amount_product': 1})

        # The items (key, value) of the current informs are used as a key to the cached_db_slot
        # tuple_current_informs = copy.deepcopy(current_informs)
        # if 'amount_product' not in tuple_current_informs:
        #     tuple_current_informs.update({'amount_product': '1'})
        # else:
        #     tuple_current_informs.update({'amount_product': str(tuple_current_informs['amount_product'])})
        # DEBUG_PRINT(tuple_current_informs)
        # inform_items = {k:tuple(v) for k,v in tuple_current_informs.items()}.items()
        # DEBUG_PRINT(inform_items)
        # inform_items = frozenset(inform_items)
        inform_items = frozenset(current_informs.items())
        # DEBUG_PRINT(inform_items)

        # A dict of the inform keys and their counts as stored (or not stored) in the cached_db_slot
        cache_return = self.cached_db_slot[inform_items]
        # DEBUG_PRINT(cache_return)

        if cache_return:
            return cache_return

        # If it made it down here then a new query was made and it must add it to cached_db_slot and return it
        # Init all key values with 0
        # db_results_slots = {key: 0.0 for key in update_current_informs.keys()}
        db_results_slots = {key: 0.0 for key in current_informs.keys()}
        db_results_slots['matching_all_constraints'] = 0

        # db_results is a dict of dict in the same exact format as the db, it is just a subset of the db
        # db_results = self._get_db_results(tuple_current_informs)
        # DEBUG_PRINT("db_results = ", db_results)
        for data in self.database:
            all_slots_match = True
            for CI_key, CI_value in current_informs.items():
                # Skip if a no query item and all_slots_match stays true
                if CI_key in self.no_query:
                    continue
                # If anything all_slots_match stays true AND the specific key slot gets a +1
                if CI_value == 'anything':
                    db_results_slots[CI_key] += 1
                    continue
                if CI_key in list(data.keys()):
                    # if CI_key == "amount_product":
                    #     # DEBUG_PRINT(CI_value)
                    #     # DEBUG_PRINT(data[CI_key])
                    #     if CI_value <= data[CI_key]:
                    #         db_results_slots[CI_key] += 1
                    # elif check_match_sublist_and_substring(CI_value,data[CI_key]):
                    #     db_results_slots[CI_key] += 1
                    if CI_value.lower() == data[CI_key].lower():
                        db_results_slots[CI_key] += 1
                    else:
                        all_slots_match = False
                else:
                    all_slots_match = False
            if all_slots_match: db_results_slots['matching_all_constraints'] += 1

        # not_match = self._check_constraints(current_requests, db_results, entity_list)
        # if not_match:
            # db_results_slots['matching_all_constraints'] = 0.0

        # update cache (set the empty dict)
        self.cached_db_slot[inform_items].update(db_results_slots)
        assert self.cached_db_slot[inform_items] == db_results_slots

        return db_results_slots

    def fill_inform_slot(self, inform_slot_to_fill, current_inform_slots, entity_list):
        """
        Given the current informs/constraints fill the informs that need to be filled with values from the database.

        Searches through the database to fill the inform slots with PLACEHOLDER with values that work given the current
        constraints of the current episode.

        Parameters:
            inform_slot_to_fill (dict): Inform slots to fill with values
            current_inform_slots (dict): Current inform slots with values from the StateTracker

        Returns:
            dict: inform_slot_to_fill filled with values
        """

        # For this simple system only one inform slot should ever passed in
        assert len(inform_slot_to_fill) == 1
        key = list(inform_slot_to_fill.keys())[0]
        # DEBUG_PRINT("inform_slot_to_fill: ", inform_slot_to_fill)

        # This removes the inform we want to fill from the current informs if it is present in the current informs
        # so it can be re-queried
        current_informs = copy.deepcopy(current_inform_slots)
        current_informs.pop(key, None)

        # db_results is a dict of dict in the same exact format as the db, it is just a subset of the db
        db_results = self.get_db_results(current_informs)
        # DEBUG_PRINT(db_results)

        filled_inform = {}
        values_dict = self._count_slot_values(key, db_results)
        DEBUG_PRINT("values_dict: ", values_dict)
        if values_dict:
            # Get key with max value (ie slot value with highest count of available results)
            # filled_inform[key] = max(values_dict, key=values_dict.get)
            if len(list(values_dict.keys())) > 1:
                filled_inform[key] = list(values_dict.keys())
            else:
                filled_inform[key] = list(values_dict.keys())[0]
        else:
            filled_inform[key] = 'no match available'
        # if not db_results:
        #     filled_inform[key] = 'no match available'
        # else:
        #     not_match = self._check_constraints(key, db_results, entity_list)
        #     # if need inform, query db, inform all of the possible value
        #     if not_match:
        #         constraints = True
        #         for constraint in entity_list[key]:
        #             # DEBUG_PRINT(constraint)
        #             # DEBUG_PRINT(current_informs)
        #             if constraint not in current_informs:
        #                 filled_inform[key] = 'no match available'
        #                 constraints = False
        #         if constraints:
        #             item = random.choice(db_results)
        #             filled_inform.update({key: item[key]})
        #     else:
        #         value = []
        #         for item in db_results:
        #             if type(item[key]) == list:
        #                 for x in item[key]:
        #                     if not value.__contains__(x):
        #                         value.append(x)
        #             else:
        #                 value.append(item[key])
        #         filled_inform.update({key: value})

        DEBUG_PRINT("result: ", filled_inform)
        return filled_inform

    def get_db_results(self, constraints):
        """
        Get all items in the database that fit the current constraints.

        Looks at each item in the database and if its slots contain all constraints and their values match then the item
        is added to the return dict.

        Parameters:
            constraints (dict): The current informs

        Returns:
            dict: The available items in the database
        """

        # Filter non-queryable items and keys with the value 'anything' since those are inconsequential to the constraints
        new_constraints = {k: v for k, v in constraints.items() if k not in self.no_query and v != 'anything'}
        
        if len(list(new_constraints.keys())) == 0:
            DEBUG_PRINT("constraints = ", constraints)
            # return []
        # if 'amount_product' not in list(new_constraints.keys()):
        #     new_constraints.update({'amount_product': 1})
        # DEBUG_PRINT("new_constraints = ", new_constraints)

        # tuple_current_informs = copy.deepcopy(new_constraints)
        # tuple_current_informs.update({'amount_product': str(tuple_current_informs['amount_product'])})
        # inform_items = {k:tuple(v) for k,v in tuple_current_informs.items()}.items()
        inform_items = frozenset(new_constraints.items())
        # DEBUG_PRINT(inform_items)

        cache_return = self.cached_db[inform_items]
        # DEBUG_PRINT(cache_return)

        if cache_return == None:
            # If it is none then no matches fit with the constraints so return an empty dict
            return []
        # if it isnt empty then return what it is
        if cache_return:
            return cache_return
        # else continue on

        # return db that contains the value of required entity
        # db_new = self.database
        # for constraint_key in list(new_constraints.keys()):
        #     db_new = self._loop(constraint_key, new_constraints[constraint_key], db_new)
        # DEBUG_PRINT(db_new)

        available_options = []
        for data in self.database:
            current_option_dict = data
            # First check if that database item actually contains the inform keys
            # Note: this assumes that if a constraint is not found in the db item then that item is not a match
            DEBUG_PRINT(set(new_constraints.keys()))
            DEBUG_PRINT(set(data.keys()))
            DEBUG_PRINT(len(set(new_constraints.keys()) - set(data.keys())))
            if len(set(new_constraints.keys()) - set(data.keys())) == 0:
                match = True
                # Now check all the constraint values against the db values and if there is a mismatch don't store
                for k, v in new_constraints.items():
                    # if k == "amount_product":
                    #     if v > data[k]:
                    #         match = False
                    # elif not check_match_sublist_and_substring(v, data[k]):
                    #     match = False
                    if str(v).lower() != str(current_option_dict[k]).lower():
                        match = False
                if match:
                    # Update cache
                    self.cached_db[inform_items].append(current_option_dict)
                    available_options.append(current_option_dict)
        # DEBUG_PRINT("available_options = ", available_options)

        # if nothing available then set the set of constraint items to none in cache
        if not available_options:
            self.cached_db[inform_items] = None

        return available_options

    def _loop(self, constraint_key, constraint_val, db):
        db_new = []
        for data in db:
            if constraint_val == 'anything':
                if constraint_key in data:
                    db_new.append(data)
            elif (constraint_key == "amount_product"):
                SAVE_LOG("constraint_val: ", constraint_val, filename='test.log')
                SAVE_LOG("data[constraint_key]: ", data[constraint_key], filename='test.log')
                if constraint_val <= data[constraint_key]:
                    db_new.append(data)
            elif (check_match_sublist_and_substring(constraint_val,data[constraint_key])):
                db_new.append(data)
        return db_new
