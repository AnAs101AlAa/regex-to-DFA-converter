import re
import argparse
from graphviz import Digraph
from collections import defaultdict
state = 0
nfa = {}

def exclusive_bracket(index, pattern):
    postfix_string = ""
    concat_flag = False
    while index < len(pattern):
        if (pattern[index] == ']'):
            return postfix_string, index
        if (index < len(pattern) - 1 and pattern[index + 1] == '-'):
            postfix_string += pattern[index]
            postfix_string += pattern[index + 2]
            postfix_string += '-'
            if concat_flag == True:
                postfix_string += "|"
            else:
                concat_flag = True
            index += 2
        else:
            if concat_flag == True:
                postfix_string += pattern[index]
                postfix_string += '|'
            else:
                concat_flag = True
                postfix_string += pattern[index]
        index += 1


def postfix_convert(index, pattern):
    postfix_string = ""
    concat_flag = 0
    i = index
    while i < len(pattern):
        # or operation
        if (pattern[i] == '|'):
            # check if group to or and collect it
            if (pattern[i + 1] == '('):
                addition, new_index = postfix_convert(i + 2, pattern)
                postfix_string += addition
                i = new_index
            else:
                postfix_string += pattern[i + 1]
                i += 1
            postfix_string += '|'

        # range operator A-Z
        elif (i < len(pattern) - 1 and pattern[i + 1] == '-'):
            postfix_string += pattern[i]
            postfix_string += pattern[i + 2]
            postfix_string += '-'
            i += 2

        # go collect group
        elif (pattern[i] == '('):
            addition, new_index = postfix_convert(i + 1, pattern)
            i = new_index
            postfix_string += addition
            concat_flag += 1

        # closing group (end recursive call)
        elif (pattern[i] == ')'):
            return postfix_string, i

        # go collect or group
        elif (pattern[i] == '['):
            addition, new_index = exclusive_bracket(i + 1, pattern)
            postfix_string += addition
            i = new_index
            concat_flag += 1
            i += 1
            continue

        # uni operators and any other character
        else:
            if i < len(pattern) - 1 and (pattern[i + 1] == '*' or pattern[i + 1] == '+' or pattern[i + 1] == '?'):
                postfix_string += pattern[i] + pattern[i + 1]
                concat_flag += 1
                i += 1
            elif pattern[i] == '*' or pattern[i] == '+' or pattern[i] == '?':
                postfix_string += pattern[i]
            else:
                postfix_string += pattern[i]
                concat_flag += 1
        i += 1
        if concat_flag >= 2:
            postfix_string += '!'
            concat_flag = 1

    return postfix_string


def form_state(index, pattern):
    global state
    new_state = {}
    new_state["start"] = state;
    new_state["end"] = state;
    if pattern[index] == '.':
        new_state["actions"] = [chr(i) for i in range(48, 59)] + [chr(i) for i in range(65, 92)] + [chr(i) for i in
                                                                                                    range(97, 124)]
    else:
        new_state["actions"] = [pattern[index]]

    if f"S{state}" not in nfa:
        nfa[f"S{state}"] = {
            "isTerminatingState": False,
        }

    state += 1
    return new_state


def or_op(node1, node2):
    global state
    new_state = {
        "start": state,
        "actions": []
    }

    # if both nodes are connected create new state to separate them and then connect them with usual or
    if (node1["end"] == node2["start"]):
        nfa[f"S{state}"] = {"isTerminatingState": False}
        for item in nfa[f"S{node1["end"]}"].keys():
            if item != "isTerminatingState":
                nfa[f"S{state}"][item] = nfa[f"S{node1["end"]}"][item]
        nfa[f"S{node1["end"]}"] = {"isTerminatingState": False}
        node2["start"] = state
        state += 1
        new_state["start"] = state

    # opener node to branch from
    nfa[f"S{state}"] = {
        "isTerminatingState": False,
        "epsilon": [f"S{node1["start"]}", f"S{node2["start"]}"]
    }

    # new node for branch one then epsilon into closer
    state += 1
    nfa[f"S{state}"] = {"isTerminatingState": False}
    if node1["actions"] == []:
        nfa[f"S{node1["end"]}"]["epsilon"] = [f"S{state}"]
    else:
        for item in node1["actions"]:
            nfa[f"S{node1["end"]}"][item] = [f"S{state}"]

    nfa[f"S{state}"] = {"isTerminatingState": False, "epsilon": [f"S{state + 2}"]}

    # new node for branch two then epsilon into closer
    state += 1
    nfa[f"S{state}"] = {"isTerminatingState": False}
    if node2["actions"] == []:
        nfa[f"S{node2["end"]}"]["epsilon"] = [f"S{state}"]
    else:
        for item in node2["actions"]:
            nfa[f"S{node2["end"]}"][item] = [f"S{state}"]

    nfa[f"S{state}"] = {"isTerminatingState": False, "epsilon": [f"S{state + 1}"]}

    # create closer for branches
    state += 1
    nfa[f"S{state}"] = {"isTerminatingState": False}

    new_state["end"] = state
    state += 1
    return new_state


def zero_more_op(node):
    global state
    new_state = {
        "start": node["start"],
        "end": state,
        "actions": []
    }
    nfa[f"S{state}"] = {"isTerminatingState": False, "epsilon": [f"S{node["start"]}"]}
    if "epsilon" in nfa[f"S{node['start']}"]:
        nfa[f"S{node['start']}"]["epsilon"].append(f"S{state}")
    else:
        nfa[f"S{node['start']}"].update({"epsilon": [f"S{state}"]})
    state += 1
    return new_state


def zero_one_op(node):
    global state
    new_state = {
        "start": node["start"],
        "end": state,
        "actions": []
    }
    nfa[f"S{state}"] = {"isTerminatingState": False}
    if "epsilon" in nfa[f"S{node['start']}"]:
        nfa[f"S{node['start']}"]["epsilon"].append(f"S{state}")
    else:
        nfa[f"S{node['start']}"].update({"epsilon": [f"S{state}"]})  
    state += 1
    return new_state


def one_more_op(node):
    global state
    new_state = {
        "start": node["start"],
        "end": state,
        "actions": []
    }

    nfa[f"S{state}"] = {"isTerminatingState": False, "epsilon": [f"S{node["start"]}"]}
    nfa[f"S{node["start"]}"].update({node["actions"][0]: [f"S{state}"]})
    state += 1
    return new_state


def concat_op(node1, node2):
    global state
    new_node = {
        "start": node1["start"],
        "end": node2["end"],
        "actions": []
    }
    if f"S{state}" not in nfa:
        nfa[f"S{state}"] = {
            "isTerminatingState": False,
        }

    if node1["actions"] == []:
        if node2["actions"] == []:
            nfa[f"S{node1["end"]}"].update({"epsilon": [f"S{node2["start"]}"]})
        for action in node2["actions"]:
            nfa[f"S{node1["end"]}"].update({action: [f"S{node2["start"]}"]})
        return new_node

    for action in node1["actions"]:
        nfa[f"S{node1["end"]}"].update({action: [f"S{node2["start"]}"]})

    for action in node2["actions"]:
        nfa[f"S{node2["end"]}"].update({action: [f"S{state}"]})
        new_node["actions"].append(action)
    return new_node


def convert_nfa(pattern):
    global nfa, state
    state_stack = []
    index = 0

    while index < len(pattern):
        if pattern[index] == '|':
            node2 = state_stack.pop()
            node1 = state_stack.pop()
            new_state = or_op(node1, node2)
            state_stack.append(new_state)

        elif pattern[index] == '-':
            upper_limit = state_stack.pop()
            lower_limit = state_stack.pop()
            new_actions = []
            for action in range(ord(lower_limit["actions"][0]), ord(upper_limit["actions"][0]) + 1):
                new_actions.append(chr(action))
            new_state = {
                "start": lower_limit["start"],
                "end": lower_limit["start"],
                "actions": new_actions
            }
            state_stack.append(new_state)
            state -= 1

        elif pattern[index] == '.':
            new_actions = []
            for action in range(ord('A'), ord('Z')+1):
                new_actions.append(chr(action))
            for action in range(ord('a'), ord('z')+1):
                new_actions.append(chr(action))
            for action in range(ord('0'), ord('9')+1):
                new_actions.append(chr(action))
            new_state = {
                "start": state,
                "end": state,
                "actions": new_actions
            }
            state_stack.append(new_state)

        elif pattern[index] == '*':
            node = state_stack.pop()
            new_state = zero_more_op(node)
            state_stack.append(new_state)

        elif pattern[index] == '+':
            node = state_stack.pop()
            new_state = one_more_op(node)
            state_stack.append(new_state)

        elif pattern[index] == '?':
            node = state_stack.pop()
            new_state = zero_one_op(node)
            state_stack.append(new_state)

        elif pattern[index] == '!':
            node2 = state_stack.pop()
            node1 = state_stack.pop()
            new_node = concat_op(node1, node2)
            state_stack.append(new_node)
        else:
            state_stack.append(form_state(index, pattern))
        index += 1
    last_element = state_stack.pop()
    nfa["startingState"] = f"S{last_element["start"]}"
    if f"S{last_element['end']}" not in nfa:
        nfa[f"S{last_element['end']}"] = {"isTerminatingState": True}
    else:
        max_state = last_element['end']
        for action, states in nfa[f"S{last_element['end']}"].items():
            if action != "isTerminatingState":
                for state in states:
                    state_index = int(state[1:])
                    if state_index > max_state:
                        max_state = state_index
        nfa[f"S{max_state}"]["isTerminatingState"] = True


def get_epsilon_closure(incoming_state):
    closure = [incoming_state]
    stack = [incoming_state]
    while stack:
        current_state = stack.pop()

        if "epsilon" in nfa[current_state]:
            for next_state in nfa[current_state]["epsilon"]:
                if next_state not in closure:
                    closure.append(next_state)
                    stack.append(next_state)
    return closure


def get_transitions(closure):
    transitions = {}
    for current_state in closure:
        for action, next_states in nfa[current_state].items():
            if action != "isTerminatingState" and action != "epsilon":
                if action not in transitions:
                    transitions[action] = []
                for next_state in next_states:
                    if next_state not in transitions[action]:
                        transitions[action].append(next_state)
    return transitions


def convert_intermediate_dfa():
    dfa_states_count = 0
    dfa_intermediate = {}
    starting_nfa_state = nfa["startingState"]
    starting_dfa_state = {}

    starting_dfa_state["closure"] = get_epsilon_closure(starting_nfa_state)
    starting_dfa_state["isTerminatingState"] = False
    starting_dfa_state["transitions"] = get_transitions(starting_dfa_state["closure"])
    state_name = f"State_{dfa_states_count}"
    dfa_intermediate[state_name] = starting_dfa_state
    dfa_states_count += 1

    dfa_intermediate[state_name]["isTerminatingState"] = any(
        nfa[state]["isTerminatingState"] for state in starting_dfa_state["closure"])

    i = 0
    while i < dfa_states_count:
        transtitions = dfa_intermediate[f"State_{i}"]["transitions"]
        for action in transtitions.keys():
            new_closure = []
            for state in transtitions[action]:
                # Add each state from epsilon closure only if not already in new_closure
                epsilon_states = get_epsilon_closure(state)
                for epsilon_state in epsilon_states:
                    if epsilon_state not in new_closure:
                        new_closure.append(epsilon_state)

            # Check if this closure already exists in any state
            exists = False
            for state_name, state_data in dfa_intermediate.items():
                if "closure" in state_data and set(state_data["closure"]) == set(new_closure):
                    exists = True
                    break

            if exists:
                continue

            # Create a new state name based on the current count
            new_state_name = f"State_{dfa_states_count}"
            dfa_intermediate[new_state_name] = {}
            dfa_intermediate[new_state_name]["closure"] = new_closure
            dfa_intermediate[new_state_name]["transitions"] = get_transitions(new_closure)
            dfa_intermediate[new_state_name]["isTerminatingState"] = any(
                nfa[state]["isTerminatingState"] for state in new_closure)
            dfa_states_count += 1
        i += 1

    """ for i in range(dfa_states_count):
        print("\n")
        print(f"State_{i}", dfa_intermediate[f"State_{i}"])
        print("\n") """
    return dfa_intermediate


def convert_dfa():
    dfa_intermediate = convert_intermediate_dfa()
    dfa = {}

    for state_name, state_data in dfa_intermediate.items():
        dfa[state_name] = {
            "isTerminatingState": state_data["isTerminatingState"],
            "transitions": {}
        }

    for state_name, state_data in dfa.items():
        transitions = dfa_intermediate[state_name]["transitions"]

        for action, target_nfa_states in transitions.items():
            combined_closure = []

            for nfa_state in target_nfa_states:
                closure = get_epsilon_closure(nfa_state)
                for state in closure:
                    if state not in combined_closure:
                        combined_closure.append(state)

            for dfa_state_name, dfa_state_data in dfa_intermediate.items():
                if set(dfa_state_data["closure"]) == set(combined_closure):
                    dfa[state_name]["transitions"][action] = dfa_state_name
                    break

    return dfa



def minimize_dfa(dfa,starting_state):
    # Gather all states and the alphabet (symbols)
    states = list(dfa.keys())
    alphabet = set()
    for state in states:
        for symbol in dfa[state]["transitions"]:
            alphabet.add(symbol)

    # Partition states into accepting and non-accepting groups
    accepting = {state for state in states if dfa[state]["isTerminatingState"]}
    non_accepting = set(states) - accepting

    partition = []
    if accepting:
        partition.append(accepting)
    if non_accepting:
        partition.append(non_accepting)

    # Refinement of partitions using transition behavior
    changed = True
    while changed:
        changed = False
        new_partition = []
        # Process each group in the current partition
        for group in partition:
            if len(group) <= 1:
                new_partition.append(group)
                continue

            # Create subgroups based on each state's signature
            # Signature: tuple of (symbol, destination_group_index) for each symbol in sorted alphabet
            subgroups = {}
            for state in group:
                signature = []
                for symbol in sorted(alphabet):
                    dest = dfa[state]["transitions"].get(symbol)
                    dest_group = None
                    if dest is not None:
                        # Find the group index in partition which contains the destination
                        for idx, part in enumerate(partition):
                            if dest in part:
                                dest_group = idx
                                break
                    signature.append((symbol, dest_group))
                signature = tuple(signature)
                subgroups.setdefault(signature, set()).add(state)
            
            # If more than one subgroup is created, mark as changed
            if len(subgroups) > 1:
                changed = True
                for subgroup in subgroups.values():
                    new_partition.append(subgroup)
            else:
                new_partition.append(group)
        partition = new_partition

    # STEP 3: Build the minimized DFA
    # Map each original state to the new minimized state name
    state_mapping = {}
    minimized_dfa = {}

    # Create new state names for each group
    for idx, group in enumerate(partition):
        new_state = f"M{idx}"
        for state in group:
            state_mapping[state] = new_state
        # Use a representative state (any state) for setting up transitions and termination flag
        rep = next(iter(group))
        minimized_dfa[new_state] = {
            "isTerminatingState": dfa[rep]["isTerminatingState"],
            "transitions": {}
        }

    # Remap transitions to use new state names
    for idx, group in enumerate(partition):
        new_state = f"M{idx}"
        rep = next(iter(group))
        for symbol in sorted(alphabet):
            dest = dfa[rep]["transitions"].get(symbol)
            if dest is not None:
                minimized_dfa[new_state]["transitions"][symbol] = state_mapping[dest]

    print(state_mapping)
    return minimized_dfa, state_mapping[starting_state]

def compress_symbols(symbols):
    """
    Compress a list of single-character symbols into ranges where possible.
    Example: ['a', 'b', 'c', 'e'] => ['a-c', 'e']
    """
    symbols = sorted(symbols)
    ranges = []
    i = 0
    while i < len(symbols):
        start = ord(symbols[i])
        end = start
        while i + 1 < len(symbols) and ord(symbols[i + 1]) == end + 1:
            i += 1
            end = ord(symbols[i])
        if start == end:
            ranges.append(chr(start))
        elif end == start + 1:
            ranges.append(chr(start))
            ranges.append(chr(end))
        else:
            ranges.append(f"{chr(start)}-{chr(end)}")
        i += 1
    return ranges


def draw_dfa(dfa, initial_state, filename='dfa_graph', view=True):
    """
    Draws a DFA using Graphviz, grouping transitions with the same destination
    and compressing character sequences into ranges like [a-c].
    """
    dot = Digraph(format='png')
    dot.attr(rankdir='LR')  # Left-to-right layout

    # Optional invisible start node
    dot.node('', shape='none')

    # Create nodes
    for state, info in dfa.items():
        shape = 'doublecircle' if info['isTerminatingState'] else 'circle'
        dot.node(state, shape=shape)

    # Group transitions: { (src, dst): [symbols] }
    grouped_edges = defaultdict(list)

    for state, info in dfa.items():
        for symbol, dest in info['transitions'].items():
            grouped_edges[(state, dest)].append(symbol)

    # Draw grouped edges with compressed symbol labels
    for (src, dst), symbols in grouped_edges.items():
        compressed = compress_symbols(symbols)
        label = "[" + ", ".join(compressed) + "]"
        dot.edge(src, dst, label=label)

    # Arrow to initial state
    dot.edge('', initial_state)

    # Render and view
    dot.render(filename, view=view)


def draw_nfa( filename='nfa_graph', view=True):
    """
    Draws an NFA using Graphviz, adapted for this input format:
    {
        'S0': {'isTerminatingState': True, 'a': ['S1'], ...},
        'S1': {'isTerminatingState': False},
        'startingState': 'S0'
    }
    """
    dot = Digraph(format='png')
    dot.attr(rankdir='LR')

    starting_state = nfa['startingState']
    dot.node('', shape='none')  # invisible starting point

    # Create nodes
    for state, info in nfa.items():
        if state == 'startingState':
            continue
        shape = 'doublecircle' if info.get('isTerminatingState', False) else 'circle'
        dot.node(state, shape=shape)

    # Group transitions: { (src, dst): [symbols] }
    grouped_edges = defaultdict(list)

    for src_state, info in nfa.items():
        if src_state == 'startingState':
            continue
        for symbol, dests in info.items():
            if symbol == 'isTerminatingState':
                continue
            for dst in dests:
                grouped_edges[(src_state, dst)].append(symbol)

    # Draw edges
    for (src, dst), symbols in grouped_edges.items():
        # Separate epsilon transitions
        epsilons = [s for s in symbols if s == 'epsilon']
        others = [s for s in symbols if s != 'epsilon']

        if others:
            compressed = compress_symbols(others)
            label = "[" + ", ".join(compressed) + "]"
            dot.edge(src, dst, label=label)

        for _ in epsilons:
            dot.edge(src, dst, label="ε")

    dot.edge('', starting_state)  # initial arrow

    dot.render(filename, view=view)

def main():
    postfix_string = postfix_convert(0, "(a|b)*[a-r]+m")
    convert_nfa(postfix_string)
    print("NFA:")
    for state, data in nfa.items():
        print(f"{state}: {data}")
    print("\n")
    dfa = convert_dfa()
    print("DFA:")
    for state, data in dfa.items():
        print(f"{state}: {data}")
        print("\n")

    minimized_dfa,starting_state = minimize_dfa(dfa,"State_0")
    print("Minimized DFA:")
    for state, data in minimized_dfa.items():
        print(f"{state}: {data}")
        print("\n")

    print("Starting state of minimized DFA:", starting_state)

    print("Final DFA:", minimized_dfa)
    draw_nfa()
    draw_dfa(minimized_dfa, starting_state, filename='dfa_graph', view=True)

if __name__ == "__main__":
    main()