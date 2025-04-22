import json
import csv
from collections import OrderedDict


class fpTreeNode:
    def __init__(self, name, freq, parent):
        self.name = name
        self.freq = freq
        self.parent = parent
        self.child = OrderedDict()
        self.link = None

    def display_tree_list(self):
        print(self.name, self.freq, end='')
        if len(self.child) > 0:
            print(",[", end='')
        for c in self.child.values():
            print("[", end='')
            c.display_tree_list()
            if len(c.child) == 0:
                print("]", end='')
        print("]", end='')


def similar_item_table_update(similar_item, present_node):
    while similar_item.link is not None:
        similar_item = similar_item.link
    similar_item.link = present_node


def fp_tree_preprocess(doc_name, threshold):
    with open(doc_name, 'r') as f:
        transactions_data = json.load(f)

    if isinstance(transactions_data[0], dict) and "items" in transactions_data[0]:
        transactions = [t["items"] for t in transactions_data]
    else:
        transactions = transactions_data

    item_freq = {}
    for transaction in transactions:
        for item in transaction:
            if item != '':
                item_freq[item] = item_freq.get(item, 0) + 1

    item_freq = {k: v for k, v in item_freq.items() if v >= threshold}
    return transactions, item_freq


def fp_tree_reorder(data, item_freq):
    root = fpTreeNode('Root', 1, None)
    sorted_items = sorted(item_freq.items(), key=lambda x: (-x[1], x[0]))

    sorted_keys = [k for k, _ in sorted_items]
    header_table = {k: None for k in sorted_keys}

    for row in data:
        transaction = [item for item in row if item in item_freq]
        ordered_transaction = [item for item in sorted_keys if item in transaction]
        if ordered_transaction:
            insert_tree(ordered_transaction, root, header_table)

    return root, header_table


def insert_tree(items, node, header_table):
    first = items[0]
    if first in node.child:
        node.child[first].freq += 1
    else:
        node.child[first] = fpTreeNode(first, 1, node)
        if header_table[first] is None:
            header_table[first] = node.child[first]
        else:
            similar_item_table_update(header_table[first], node.child[first])

    remaining_items = items[1:]
    if remaining_items:
        insert_tree(remaining_items, node.child[first], header_table)


def find_prefix_paths(base_pat, node):
    cond_pats = []
    while node is not None:
        path = []
        parent = node.parent
        while parent is not None and parent.name != 'Root':
            path.append(parent.name)
            parent = parent.parent
        if path:
            cond_pats.append((list(reversed(path)), node.freq))
        node = node.link
    return cond_pats


def conditional_fptree(cond_pats, threshold):
    item_freq = {}
    for path, freq in cond_pats:
        for item in path:
            item_freq[item] = item_freq.get(item, 0) + freq

    item_freq = {k: v for k, v in item_freq.items() if v >= threshold}
    if not item_freq:
        return None, None

    root = fpTreeNode('Root', 1, None)
    header_table = {k: None for k in sorted(item_freq, key=lambda k: -item_freq[k])}

    for path, freq in cond_pats:
        ordered_items = [item for item in sorted(item_freq, key=lambda k: -item_freq[k]) if item in path]
        if ordered_items:
            insert_cond_tree(ordered_items, root, header_table, freq)

    return root, header_table


def insert_cond_tree(items, node, header_table, freq):
    first = items[0]
    if first in node.child:
        node.child[first].freq += freq
    else:
        node.child[first] = fpTreeNode(first, freq, node)
        if header_table[first] is None:
            header_table[first] = node.child[first]
        else:
            similar_item_table_update(header_table[first], node.child[first])

    remaining_items = items[1:]
    if remaining_items:
        insert_cond_tree(remaining_items, node.child[first], header_table, freq)


def mine_fp_tree(header_table, threshold, prefix, frequent_itemsets):
    for base_pat in sorted(header_table, key=lambda k: k):
        new_freq_set = prefix + [base_pat]
        support = 0
        node = header_table[base_pat]
        while node is not None:
            support += node.freq
            node = node.link
        frequent_itemsets.append((new_freq_set, support))

        cond_pats = find_prefix_paths(base_pat, header_table[base_pat])
        cond_tree, cond_header = conditional_fptree(cond_pats, threshold)
        if cond_header is not None:
            mine_fp_tree(cond_header, threshold, new_freq_set, frequent_itemsets)


def export_to_file(data, output_file_name):
    print(f"Exporting {len(data)} itemsets to {output_file_name}")
    if not data:
        print("No data to write.")
        return
    with open(output_file_name, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Itemset", "Support"])
        for itemset, support in data:
            writer.writerow([", ".join(itemset), support])


# --- Main Execution ---
support = 10
file_name = 'TBD3.json'
output_file_name = "output.csv"

dataset, freq_items = fp_tree_preprocess(file_name, support)
fptree_root, header_table = fp_tree_reorder(dataset, freq_items)

frequent_itemsets = []
mine_fp_tree(header_table, support, [], frequent_itemsets)

export_to_file(frequent_itemsets, output_file_name)
