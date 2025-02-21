# functions for command line interaction


def confirm_action(prompt=None):
    if prompt is not None:
        print(prompt)
    print("press enter to continue, or type something and then press enter to abort")
    inp = input()
    return inp == ""

