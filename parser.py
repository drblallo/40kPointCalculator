import re
from collections import defaultdict
from difflib import get_close_matches
from argparse import ArgumentParser
import argparse, os


def file_path(string):
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)


def parse_40k_data(lines):
    # Initialize the current faction and unit
    current_faction = None
    current_unit = None

    # Initialize the list of parsed data
    parsed_data = []

    # Iterate over the lines
    for i in range(len(lines)):
        line = lines[i].strip()

        # If the line is empty, skip it
        if not line:
            continue

        # If the line contains 'pts', it is a model line
        if "pts" in line:
            # Extract the number of models and the cost
            match = re.search(r"(\d+) models?.*?(\d+) pts", line)
            if match:
                num_models, cost = match.groups()
            else:
                # If no model count is specified, assume 1
                match = re.search(r"(.*?)(\d+) pts", line)
                num_models = "1"
                current_unit, cost = match.groups()
                current_unit = current_unit.strip()

            # Add the parsed data to the list
            parsed_data.append((current_faction, current_unit, num_models, cost))

        # If the line does not contain 'pts', it is a faction or unit line
        else:
            # If there is no current faction, this line is a faction
            if current_faction is None:
                current_faction = line
            # If the next line also does not contain 'pts', this line is a new faction
            elif i + 1 < len(lines) and "pts" not in lines[i + 1]:
                current_faction = line
            # Otherwise, this line is a unit
            else:
                current_unit = line

    # Return the parsed data
    return parsed_data


def get_cost_table(file):
    with open(file) as f:
        parsed_data = parse_40k_data(f.readlines())

        table = defaultdict(lambda: defaultdict(list))
        for faction, unit, num_models, cost in parsed_data:
            table[faction][unit].append((num_models, cost))
        return table


def get_user_list(file):
    list = []
    faction = None
    with open(file) as f:
        lines = f.readlines()

        for line in lines:
            if faction is None:
                faction = line.strip()
                continue

            if line.strip() == "":
                continue

            match = re.search(r"(\d+)(.*)", line)
            if match:
                num_models, name = match.groups()
                list.append((num_models, name))
            else:
                match = re.search(r"(.*)", line)
                name = match.group(1)
                list.append((1, name))

    return faction, list


def get_cost(quantiy, name, cost_table):
    best_possibles = get_close_matches(name, cost_table.keys(), 1, 0)
    if len(best_possibles) == 0:
        print(f"could not find any unit named {name}")
        exit()

    best_possible = best_possibles[0]
    entries = cost_table[best_possible]
    for table_quantity, cost in entries:
        if int(quantiy) <= int(table_quantity):
            return (table_quantity, best_possible, cost)

    print(f"models count for unit {quantiy} {name} was too great")
    exit()

def main():
    parser = ArgumentParser()
    parser.add_argument("--point-cost-file", type=file_path, default="./points.txt")
    parser.add_argument("list", type=file_path)
    args = parser.parse_args()

    table = get_cost_table(args.point_cost_file)
    faction, list = get_user_list(args.list)

    maybe_faction = get_close_matches(faction, table.keys(), 1, 0)
    if len(maybe_faction) == 0:
        print(f"no known faction {faction}")

    faction = maybe_faction[0]

    real_list = [get_cost(quantity, name, table[faction]) for quantity, name in list]

    total_cost = sum([int(cost) for quantiy, name, cost in real_list])
    print(f"{faction:16}: {total_cost:>29}")
    for (quantiy, name, cost) in real_list:
        print(f"{quantiy:>2} {name:40}{cost:>4}")

# Test the function
if __name__ == "__main__":
    main()
