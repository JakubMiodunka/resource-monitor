import argparse
import curses
import curses.textpad as textpad
import psutil

######################################
#       Author: Jakub Miodunka       #
#            Version: 1              #
#       Last update: 21.11.2022      #
#   Used version of Python: 3.8.10   #
######################################

class BarGraph:
    """
        Class used for creating bar graphs in terminal window
        created in use of curses.wondow type object.
    """

    def __init__(self, stdscr: curses.window, pos_y: int, pos_x: int, label: str) -> None:
        """
        After init graph will be displayed with value equal to 0%.
        It can be updated by direct call of class instance.
            Graph dimensions:
                Width: 26 + <label length>
                Height: 3
            Arguments:
                stdscr - window that should be used by class instance
                pos_y - Y coordinate of left top corner of the graph
                pos_x - X coordinate of left top corner of the graph
                label - graph label content
        """
        # Properties init
        self.stdscr = stdscr                    # Window using by class instance
        self.pointer_y = pos_y                  # Y axis coordinate of space used by pointer
        self.pointer_x = pos_x + len(label) + 1 # X axis coordinate of space used by pointer
        self.bar_y = pos_y + 1                  # Y axis coordinate of point where bar starts
        self.bar_x = pos_x + len(label) + 2     # X axis coordinate of point where bar starts

        # Printing pointer
        self.stdscr.addstr(self.pointer_y, self.pointer_x, "┌0%")

        # Printing label along with opening braces
        self.stdscr.addstr(self.bar_y, pos_x, f"{label} |" + "░" * 19 + "|")

        # Printing scale
        self.stdscr.addstr(self.bar_y + 1, self.bar_x - 1, "0")
        self.stdscr.addstr(self.bar_y + 1, self.bar_x + 18, "100")

        # Window refresh
        self.stdscr.refresh()

    def __call__(self, value: int) -> None:
        """
            Direct call of class instance will update value displayed by the graph.
                Arguments:
                    value - new value. Should be in range <0;100>
        """

        # Arguments valdation
        assert 0 <= value <= 100, "Given value not in range <0;100>"

        # Rounding given value
        value = round(value)

        # Determining how many bar blocks shuld be displayed
        blocks = int(value / 5)

        # Erasing row where pointer is displayed
        self.stdscr.addstr(self.pointer_y, self.pointer_x, f"{'':25}")

        # Printing new pointer according to given value
        self.stdscr.addstr(self.pointer_y, self.pointer_x + blocks, f"┌{value}%")
        
        # Printing bar blocks
        if value != 100:
            # Printing bar blocks according to previously calculated value
            self.stdscr.addstr(self.bar_y, self.bar_x, "█" * blocks + "░" * (19-blocks))
        else:
            # If bar will show 100% last block should not be displayed - only cursor should move
            self.stdscr.addstr(self.bar_y, self.bar_x, "█" * (blocks-1))

       # Window refresh
        self.stdscr.refresh()


# Functions realted to basic mode
def basic_init(stdscr: curses.window) -> None:
    # Creating frame
    textpad.rectangle(stdscr, 0, 0, 4, 63)

    # Adding label
    stdscr.addstr(0, 2, " Basic ")

    # Creating grphs
    cpu_graph = BarGraph(stdscr, 1, 3, "CPU")
    ram_graph = BarGraph(stdscr, 1, 34, "RAM")

    # Retuning graphs for further operations
    return cpu_graph, ram_graph

def basic_update(cpu_graph: BarGraph, ram_graph: BarGraph) -> None:
    # Updating cpu graph
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_graph(cpu_usage)

    # Updating memory graph
    mem_stats = psutil.virtual_memory()
    ram_usage = round((mem_stats.total-mem_stats.available) / mem_stats.total * 100)
    ram_graph(ram_usage)

# Functions related to advanced mode
def advanced_init(stdscr: curses.window) -> None:
    # Determining how many rows will be needed to display all graphs
    rows = int(psutil.cpu_count() / 2)

    # Creating frame
    textpad.rectangle(stdscr, 5, 0, 6 + 3 * rows, 63)

    # Adding label
    stdscr.addstr(5, 2, " Advanced ")

    # Creating list where all created graphs will be stored
    cpu_graphs = list()

    # Creating graphs
    cpu_id = 1              # Used to create graphs labels
    for row in range(rows):
        # Computing row coordinate on Y axis
        row_y = 3 * row

        # Creating graphs placed on left site
        left_graph = BarGraph(stdscr, row_y + 6, 1, f"CPU{cpu_id:<2}")
        cpu_graphs.append(left_graph)
        cpu_id += 1

        # Creating graphs placed on right site
        right_graph = BarGraph(stdscr, row_y + 6, 32, f"CPU{cpu_id:<2}")
        cpu_graphs.append(right_graph)
        cpu_id += 1

    # Returning created graphs
    return tuple(cpu_graphs)

def advanced_update(cpu_graphs: tuple) -> None:
    # Collecting data about usage of each CPU core
    usage_per_cpu = psutil.cpu_percent(interval=1, percpu=True)

    # VAlidation if collected data corresponds to graf tuple given in argument
    assert len(cpu_graphs) == len(usage_per_cpu), "Quantity of graphs do not match quantity of CPUs"

    # Updating each graph with corresponding value
    for graph, cpu_usage in zip(cpu_graphs, usage_per_cpu):
        graph(cpu_usage)

# Main part of the script
def main(stdscr, advanced_mode: bool) -> None:
    # Basic section init
    cpu_graph, ram_graph = basic_init(stdscr)

    # Updating displayed values
    try:
        if advanced_mode:
            # Advanced section init
            cpu_graphs = advanced_init(stdscr)

            while True:
                basic_update(cpu_graph, ram_graph)
                advanced_update(cpu_graphs)
        else:
            while True:
                basic_update(cpu_graph, ram_graph)

    except KeyboardInterrupt:
        exit(0)

if __name__ == "__main__":
    # Parsing arguments
    parser = argparse.ArgumentParser(description="Simple resource monitor.")
    parser.add_argument("-a", "--advanced", action="store_true", help="Advanced mode where usage of each CPU is displayed individually.")
    args = parser.parse_args()

    # Wrapping main function
    try:
        curses.wrapper(main, args.advanced)
    except curses.error:
        raise curses.error("Terminal window is too small to handle this program properly. Please maximize terminal window.")
