# functions for command line interaction


def confirm_action(prompt):
    # empty input defaults to yes, any input other than y or Y defaults to no.
    print(prompt)
    print("Type [y/n] and press enter: ")
    inp = input()
    return (inp == "") or (inp.upper() == "Y")
