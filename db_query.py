from collections import defaultdict
import copy
import random

from utils import DEBUG_PRINT, SAVE_LOG
from utils import check_match_sublist_and_substring
from dialogue_config import no_query_keys, usersim_default_key, size_slots

class DBQuery:
    """Queries the database for the state tracker."""

    def __init__(self, database, size_database):
        """
        The constructor for DBQuery.

        Parameters:
            database (dict): The database in the format dict(long: dict)
        """

        self.database = database
        self.size_database = size_database
        # {frozenset: {string: int}} A dict of dicts
        self.cached_db_slot = defaultdict(dict)
        self.cached_size_db_slot = defaultdict(dict)
        # {frozenset: {'#': {'slot': 'value'}}} A dict of dicts of dicts, a dict of DB sub-dicts
        self.cached_db = defaultdict(list)
        self.cached_size_db = defaultdict(list)
        self.no_query = no_query_keys
        self.match_key = usersim_default_key
        self.size_slots = size_slots

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
                # base on val of it, get val of request key
                if len(val_list) > 1:
                    val_request_key = []
                    for i, val in enumerate(val_list):
                        val_request_key.append(None)
                        val_request_key[i] = []
                        for data in db_results:
                            if val == data[entity] and not val_request_key[i].__contains__(data[request_key]):
                                val_request_key[i].append(data[request_key])
                    check = val_request_key[0]
                    for val in val_request_key[1:]:
                        if not check_match_sublist_and_substring(val, check):
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
        Parameters:
            current_inform_slots (dict): The current informs/constraints

        Returns:
            dict: Each key in current_informs with the count of the number of matches for that key
        """

        product_db_results_slots = self.get_db_results_for_product_slots(current_informs)
        DEBUG_PRINT('product_db_results_slots = ', product_db_results_slots)

        size_db_results_slots = self.get_db_results_for_size_slots(current_informs)
        DEBUG_PRINT('size_db_results_slots = ', size_db_results_slots)

        # If it made it down here then a new query was made and it must add it to cached_db_slot and return it
        # Init all key values with 0
        db_results_slots = {key: 0.0 for key in current_informs.keys()}
        db_results_slots['matching_all_constraints'] = 0

        db_results_slots.update(product_db_results_slots)
        for key, value in size_db_results_slots.items():
            if key == 'matching_all_constraints':
                continue
            elif key == 'size_customer':
                continue
            else:
                db_results_slots.update({key: value})

        return db_results_slots

    def get_db_results_for_product_slots(self, current_informs):
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

        # Filter non-queryable items and keys with the value 'anything' since those are inconsequential to the constraints
        new_current_informs = {k: v for k, v in current_informs.items() \
            if k not in self.size_slots}

        inform_items = frozenset(new_current_informs.items())
        # DEBUG_PRINT(inform_items)

        # A dict of the inform keys and their counts as stored (or not stored) in the cached_db_slot
        cache_return = self.cached_db_slot[inform_items]
        # DEBUG_PRINT(cache_return)

        if cache_return:
            return cache_return

        # If it made it down here then a new query was made and it must add it to cached_db_slot and return it
        # Init all key values with 0
        db_results_slots = {key: 0.0 for key in new_current_informs.keys()}
        db_results_slots['matching_all_constraints'] = 0

        # db_results is a dict of dict in the same exact format as the db, it is just a subset of the db
        # DEBUG_PRINT("db_results = ", db_results)
        for data in self.database:
            all_slots_match = True
            for CI_key, CI_value in new_current_informs.items():
                # Skip if a no query item and all_slots_match stays true
                if CI_key in self.no_query:
                    continue
                # If anything all_slots_match stays true AND the specific key slot gets a +1
                if CI_value == 'anything':
                    db_results_slots[CI_key] += 1
                    continue
                if CI_key in list(data.keys()):
                    if CI_value.lower() == data[CI_key].lower():
                        db_results_slots[CI_key] += 1
                    else:
                        all_slots_match = False
                else:
                    all_slots_match = False
            if all_slots_match: db_results_slots['matching_all_constraints'] += 1

        # update cache (set the empty dict)
        self.cached_db_slot[inform_items].update(db_results_slots)
        assert self.cached_db_slot[inform_items] == db_results_slots

        return db_results_slots

    def get_db_results_for_size_slots(self, current_informs):
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

        # Filter non-queryable items and keys with the value 'anything' since those are inconsequential to the constraints
        new_current_informs = {k: v for k, v in current_informs.items() \
            if k in self.size_slots}
        if 'size_product' in list(current_informs.keys()):
            new_current_informs['size_customer'] = current_informs['size_product']

        inform_items = frozenset(new_current_informs.items())
        # DEBUG_PRINT(inform_items)

        # A dict of the inform keys and their counts as stored (or not stored) in the cached_db_slot
        cache_return = self.cached_size_db_slot[inform_items]
        # DEBUG_PRINT(cache_return)

        if cache_return:
            return cache_return

        # If it made it down here then a new query was made and it must add it to cached_db_slot and return it
        # Init all key values with 0
        db_results_slots = {key: 0.0 for key in new_current_informs.keys()}
        db_results_slots['matching_all_constraints'] = 0

        # db_results is a dict of dict in the same exact format as the db, it is just a subset of the db
        # DEBUG_PRINT("db_results = ", db_results)
        for data in self.size_database:
            all_slots_match = True
            for CI_key, CI_value in new_current_informs.items():
                # Skip if a no query item and all_slots_match stays true
                if CI_key in self.no_query:
                    continue
                # If anything all_slots_match stays true AND the specific key slot gets a +1
                if CI_value == 'anything':
                    db_results_slots[CI_key] += 1
                    continue
                if CI_key in list(data.keys()):
                    if CI_value.lower() == data[CI_key].lower() or data[CI_key] == 'anything':
                        db_results_slots[CI_key] += 1
                    else:
                        all_slots_match = False
                else:
                    all_slots_match = False
            if all_slots_match: db_results_slots['matching_all_constraints'] += 1

        # update cache (set the empty dict)
        self.cached_size_db_slot[inform_items].update(db_results_slots)
        assert self.cached_size_db_slot[inform_items] == db_results_slots

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
        size_current_informs = copy.deepcopy(current_inform_slots)
        size_current_informs.pop(key, None)

        size_customer = ''
        if key == 'size_product':
            size_db_results = self.get_size_db_results(size_current_informs)
            if size_db_results == -1:
                size_customer = ''
            elif size_db_results:
                # DEBUG_PRINT("db_results size = ", db_results)
                size_values_dict = self._count_slot_values('size_customer', size_db_results)
                DEBUG_PRINT("size_values_dict: ", size_values_dict)
                if size_values_dict:
                    # Get key with max value (ie slot value with highest count of available results)
                    size_customer = list(size_values_dict.keys())[0]
                    if len(list(size_values_dict.keys())) > 1:
                        if 'waist_customer' in size_current_informs and 'height_customer' in size_current_informs and 'weight_customer' in size_current_informs:
                            size_customer = max(size_values_dict, key=size_values_dict.get)
                        else:
                            size_customer = list(size_values_dict.keys())
                    DEBUG_PRINT("size_customer = ", size_customer)
                else:
                    size_customer = 'no match available'
            else:
                size_customer = 'no match available'

        current_informs = copy.deepcopy(current_inform_slots)
        current_informs.pop(key, None)

        filled_inform = {}
        if size_customer == 'no match available':
            filled_inform[key] = 'no match available'
        else:
            # db_results is a dict of dict in the same exact format as the db, it is just a subset of the db
            db_results = self.get_product_db_results(current_informs)
            # DEBUG_PRINT(db_results)

            values_dict = self._count_slot_values(key, db_results)
            DEBUG_PRINT("values_dict: ", values_dict)
            if values_dict:
                # Get key with max value (ie slot value with highest count of available results)
                if key == 'size_product' and size_customer != '':
                    if type(size_customer) == list:
                        if check_match_sublist_and_substring(size_customer, list(values_dict.keys())):
                            filled_inform[key] = size_customer
                        else:
                            filled_inform[key] = list(values_dict.keys())
                    elif size_customer in list(values_dict.keys()):
                        filled_inform[key] = size_customer
                    elif size_customer not in list(values_dict.keys()):
                        filled_inform[key] = 'no match available'
                elif len(list(values_dict.keys())) > 1:
                    filled_inform[key] = list(values_dict.keys())
                else:
                    filled_inform[key] = list(values_dict.keys())[0]
            else:
                filled_inform[key] = 'no match available'

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

        current_informs = copy.deepcopy(constraints)

        size_customer = ''
        if 'size_product' not in list(current_informs.keys()):
            size_db_results = self.get_size_db_results(current_informs)
            if size_db_results == -1:
                size_customer = ''
            elif size_db_results:
                # DEBUG_PRINT("db_results size = ", db_results)
                size_values_dict = self._count_slot_values('size_customer', size_db_results)
                DEBUG_PRINT("size_values_dict: ", size_values_dict)
                if size_values_dict:
                    # Get key with max value (ie slot value with highest count of available results)
                    size_customer = list(size_values_dict.keys())[0]
                    if len(list(size_values_dict.keys())) > 1:
                        if 'waist_customer' in list(current_informs.keys()) and 'height_customer' in list(current_informs.keys()) and 'weight_customer' in list(current_informs.keys()):
                            size_customer = max(size_values_dict, key=size_values_dict.get)
                        else:
                            size_customer = ''
                    DEBUG_PRINT("size_customer = ", size_customer)
                else:
                    size_customer = 'no match available'
            else:
                size_customer = 'no match available'

        if size_customer == 'no match available':
            current_informs.update({'size_product': 'no match available'})
        elif size_customer != '':
            current_informs.update({'size_product': size_customer})
        return self.get_product_db_results(current_informs)

    def get_product_db_results(self, constraints):
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
        new_constraints = {k: v for k, v in constraints.items() \
            if k not in self.no_query and v != 'anything' and k not in self.size_slots}

        if len(list(new_constraints.keys())) == 0:
            DEBUG_PRINT("constraints = ", constraints)

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

        available_options = []
        for data in self.database:
            current_option_dict = data
            # First check if that database item actually contains the inform keys
            # Note: this assumes that if a constraint is not found in the db item then that item is not a match
            # DEBUG_PRINT(set(new_constraints.keys()))
            # DEBUG_PRINT(set(data.keys()))
            # DEBUG_PRINT(len(set(new_constraints.keys()) - set(data.keys())))
            if len(set(new_constraints.keys()) - set(data.keys())) == 0:
                match = True
                # Now check all the constraint values against the db values and if there is a mismatch don't store
                for k, v in new_constraints.items():
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

    def get_size_db_results(self, constraints):
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
        new_constraints = {k: v for k, v in constraints.items() \
            if k not in self.no_query and v != 'anything' and k in self.size_slots}
        
        if len(list(new_constraints.keys())) == 0:
            DEBUG_PRINT("constraints = ", constraints)
            return -1

        inform_items = frozenset(new_constraints.items())
        # DEBUG_PRINT(inform_items)

        cache_return = self.cached_size_db[inform_items]
        # DEBUG_PRINT(cache_return)

        if cache_return == None:
            # If it is none then no matches fit with the constraints so return an empty dict
            return []
        # if it isnt empty then return what it is
        if cache_return:
            return cache_return
        # else continue on

        available_options = []
        for data in self.size_database:
            current_option_dict = data
            # First check if that database item actually contains the inform keys
            # Note: this assumes that if a constraint is not found in the db item then that item is not a match
            # DEBUG_PRINT(set(new_constraints.keys()))
            # DEBUG_PRINT(set(data.keys()))
            # DEBUG_PRINT(len(set(new_constraints.keys()) - set(data.keys())))
            if len(set(new_constraints.keys()) - set(data.keys())) == 0:
                match = True
                # Now check all the constraint values against the db values and if there is a mismatch don't store
                for k, v in new_constraints.items():
                    if str(v).lower() != str(current_option_dict[k]).lower():
                        match = False
                if match:
                    # Update cache
                    self.cached_size_db[inform_items].append(current_option_dict)
                    available_options.append(current_option_dict)
        # DEBUG_PRINT("available_options = ", available_options)

        # if nothing available then set the set of constraint items to none in cache
        if not available_options:
            self.cached_size_db[inform_items] = None

        return available_options
