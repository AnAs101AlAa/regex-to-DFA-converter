import re
import argparse

state = 0
nfa = {}


def exclusive_bracket(index, pattern):
    postfix_string = ""
    concat_flag = False
    while index < len(pattern):
        if(pattern[index] == ']'):
            return postfix_string, index
        if ( index < len(pattern) -1 and pattern[index+1] == '-'):
            postfix_string += pattern[index]
            postfix_string += pattern[index+2]
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
        #check to add concat operator for each pair
        if concat_flag == 2:
            postfix_string += '!'
            concat_flag = 1

        #or operation
        if (pattern[i] == '|'):
            #check if group to or and collect it
            if(pattern[i+1] == '('):
                addition, new_index = postfix_convert(i+2, pattern)
                postfix_string += addition
                i = new_index
            else:
                postfix_string += pattern[i+1]
                i += 1
            postfix_string += '|'

        #range operator A-Z
        elif (i < len(pattern) - 1 and pattern[i+1] == '-'):
            postfix_string += pattern[i]
            postfix_string += pattern[i+2]
            postfix_string += '-'
            i += 2

        #go collect group
        elif (pattern[i] == '('):
            addition, new_index = postfix_convert(i+1, pattern)
            i = new_index
            postfix_string += addition
            concat_flag += 1
        
        #closing group (end recursive call)
        elif (pattern[i] == ')'): 
            return postfix_string, i
        
        #go collect or group
        elif (pattern[i] == '['):
            addition, new_index = exclusive_bracket(i+1, pattern)
            postfix_string += addition
            i = new_index
            concat_flag += 1
        
        #uni operators and any other character
        else:
            if i < len(pattern) - 1 and (pattern[i+1] == '*' or pattern[i+1] == '+' or pattern[i+1] == '?' ):
                postfix_string += pattern[i] + pattern[i+1]
                i += 1
            else:
                postfix_string += pattern[i]
            concat_flag += 1
        i += 1
    if concat_flag == 2:
        postfix_string += '!'

    return postfix_string

    
def form_state(index, pattern):
    global state
    new_state = {}
    new_state["start"] = state;
    new_state["end"] = state;
    if pattern[index] == '.':
        new_state["actions"] = [chr(i) for i in range(48, 58)] + [chr(i) for i in range(65, 91)] + [chr(i) for i in range(97, 123)]
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
        "start" : state,
        "actions": []
    }
    
    #if both nodes are connected create new state to separate them and then connect them with usual or
    if(node1["end"] == node2["start"]):
        nfa[f"S{state}"] = {"isTerminatingState": False}
        for item in nfa[f"S{node1["end"]}"].keys():
            if item != "isTerminatingState":
                nfa[f"S{state}"][item] = nfa[f"S{node1["end"]}"][item]
        nfa[f"S{node1["end"]}"] = {"isTerminatingState" : False}
        node2["start"] = state
        state +=1
        new_state["start"] = state

    #opener node to branch from
    nfa[f"S{state}"] = {
        "isTerminatingState": False,
        "epsilon": [f"S{node1["start"]}", f"S{node2["start"]}"]
    }

    #new node for branch one then epsilon into closer
    state += 1
    nfa[f"S{state}"] = {"isTerminatingState": False}
    if node1["actions"] == []:
        nfa[f"S{node1["end"]}"]["epsilon"] = f"S{state}"
    else:
        for item in node1["actions"]:
            nfa[f"S{node1["end"]}"][item] = f"S{state}"

    nfa[f"S{state}"] = {"isTerminatingState": False, "epsilon": f"S{state+2}"}

    #new node for branch two then epsilon into closer
    state += 1
    nfa[f"S{state}"] = {"isTerminatingState": False}
    if node2["actions"] == []:
        nfa[f"S{node2["end"]}"]["epsilon"] = f"S{state}"
    else:
        for item in node2["actions"]:
            nfa[f"S{node2["end"]}"][item] = f"S{state}"

    nfa[f"S{state}"] = {"isTerminatingState": False, "epsilon": f"S{state+1}"}

    #create closer for branches
    state +=1
    nfa[f"S{state}"] = {"isTerminatingState": False}

    new_state["end"] = state
    state +=1
    return new_state

def zero_more_op(node):
    global state
    new_state = {
        "start": node["start"],
        "end": state,
        "actions": []
    }
    nfa[f"S{state}"] = {"isTerminatingState": False, "epsilon": f"S{node["start"]}"}
    nfa[f"S{node["start"]}"].update({"epsilon": f"S{state}", node["actions"][0]: f"S{state}"})
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
    nfa[f"S{node["start"]}"].update({"epsilon": f"S{state}", node["actions"][0]: f"S{state}"})
    state +=1
    return new_state

def one_more_op(node):
    global state
    new_state = {
        "start": node["start"],
        "end": state,
        "actions": []
    }

    nfa[f"S{state}"] = {"isTerminatingState": False, "epsilon": f"S{node["start"]}"}
    nfa[f"S{node["start"]}"].update({node["actions"][0]: f"S{state}"})
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
            nfa[f"S{node1["end"]}"].update({"epsilon": f"S{node2["start"]}"})
        for action in node2["actions"]:
            nfa[f"S{node1["end"]}"].update({action: f"S{node2["start"]}"})
        return new_node
    
    for action in node1["actions"]:
        nfa[f"S{node1["end"]}"].update({action: f"S{node2["start"]}"})
    
    for action in node2["actions"]:
        nfa[f"S{node2["end"]}"].update({action: f"S{state}"})
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
            new_state = or_op(node1,node2)
            state_stack.append(new_state)

        elif pattern[index] == '-':
            upper_limit = state_stack.pop()
            lower_limit = state_stack.pop()
            new_actions = []
            for action in range(ord(lower_limit["actions"][0]), ord(upper_limit["actions"][0])+1):
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
            for action in range(ord('A'), ord('Z')):
                new_actions.append(chr(action))
            for action in range(ord('a'), ord('z')):
                new_actions.append(chr(action))
            for action in range(ord('0'), ord('9')):
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
            state_stack.append(form_state(index,pattern))
        index += 1
    last_element = state_stack.pop()
    nfa["startingState"] = f"S{last_element["start"]}"
    nfa[f"S{last_element["end"]}"]["isTerminatingState"] = True



def main():
    postfix_string = postfix_convert(0,"[A-ZBD].|(BR)f")
    convert_nfa(postfix_string)
if __name__ == "__main__":
    main()