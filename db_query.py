from collections import defaultdict
import copy
import random

from utils import DEBUG_PRINT

class DBQuery:
    """Queries the database for the state tracker."""

    def __init__(self, database):
        """
        The constructor for DBQuery.

        Parameters:
            database (dict): The database in the format dict(long: dict)
        """

        self.database = database

    def _check_match_sublist_and_substring(self, list_children, list_parent):
        count_match=0
        for children_value in list_children:
            for parent_value in list_parent:
                if children_value in parent_value:
                    count_match+=1
                    break
        if count_match==len(list_children):
            return True
        return False

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
                        if check != val:
                            not_match = True
                            break
        return not_match

    def get_db_results_for_slots(self, current_informs, current_requests, entity_list):
        """
        Counts occurrences of each current inform slot (key and value) in the database items.

        For each item in the database and each current inform slot if that slot is in the database item (matches key
        and value) then increment the count for that key by 1.

        If don't have any informed entity, return all 0

        Parameters:
            current_inform_slots (dict): The current informs/constraints
            current_request_slots (dict): The current request to get constraints
            entity_list (dict): The current request to get constraints

        Returns:
            dict: Each key in current_informs with the count of the number of matches for that key
        """

        tuple_current_informs=copy.deepcopy(current_informs)
        if 'amount_product' not in tuple_current_informs:
            tuple_current_informs.update({'amount_product': 1})

        # If it made it down here then a new query was made and it must add it to cached_db_slot and return it
        # Init all key values with 0
        db_results_slots = {key: 0.0 for key in tuple_current_informs.keys()}
        db_results_slots['matching_all_constraints'] = 0.0

        # db_results is a dict of dict in the same exact format as the db, it is just a subset of the db
        db_results = self._get_db_results(tuple_current_informs)
        # DEBUG_PRINT("db_results = ", db_results)
        for data in db_results:
            all_slots_match = True
            for CI_key, CI_value in tuple_current_informs.items():
                # If anything all_slots_match stays true AND the specific key slot gets a +1
                if CI_value == 'anything':
                    db_results_slots[CI_key] += 1
                    continue
                if CI_key in list(data.keys()):
                    if ((CI_key == "amount_product") and (CI_value <= data[CI_key])) or self._check_match_sublist_and_substring(CI_value,data[CI_key]):
                        db_results_slots[CI_key] += 1
                    else:
                        all_slots_match = False
                else:
                    all_slots_match = False
            if all_slots_match: db_results_slots['matching_all_constraints'] += 1

        not_match = self._check_constraints(current_requests, db_results, entity_list)
        if not_match:
            db_results_slots['matching_all_constraints'] = 0.0

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
        db_results = self._get_db_results(current_informs)

        filled_inform = {}
        not_match = self._check_constraints(key, db_results, entity_list)

        # if need inform, query db, inform all of the possible value
        if not_match:
            filled_inform[key] = 'no match available'
        elif db_results:
            value = []
            for item in db_results:
                if not value.__contains__(item[key]):
                    value.append(item[key])
            filled_inform.update({key: value})
        else:
            filled_inform[key] = 'no match available'

        # DEBUG_PRINT("result: ", filled_inform)
        return filled_inform

    def _get_db_results(self, constraints):
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
        new_constraints = {k: v for k, v in constraints.items() if v is not 'anything'}
        if 'amount_product' not in list(new_constraints.keys()):
            new_constraints.update({'amount_product': 1})
        # DEBUG_PRINT("new_constraints = ", new_constraints)

        tuple_new_constraint=copy.deepcopy(new_constraints)

        # return db that contains the value of required entity
        db_new = self.database
        for constraint_key in list(new_constraints.keys()):
            db_new = self._loop(constraint_key, new_constraints[constraint_key], db_new)

        return db_new

    def _loop(self, constraint_key, constraint_val, db):
        db_new = []
        for data in db:
            if constraint_val == 'anything':
                if constraint_key in data:
                    db_new.append(data)
            elif (constraint_val == data[constraint_key]) or ((constraint_key == "amount_product") and (constraint_val <= data[constraint_key])):
                db_new.append(data)
        return db_new
